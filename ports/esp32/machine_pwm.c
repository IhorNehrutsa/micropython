/*
 * This file is part of the Micro Python project, http://micropython.org/
 *
 * The MIT License (MIT)
 *
 * Copyright (c) 2016-2021 Damien P. George
 * Copyright (c) 2020 Antoine Aubert
 * Copyright (c) 2021 Ihor Nehrutsa
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

#include "py/runtime.h"
#include "py/mphal.h"

#include "driver/ledc.h"
#include "esp_err.h"
#include "esp_log.h"

STATIC mp_obj_t mp_machine_pwm_duty_get(machine_pwm_obj_t *self);
STATIC void mp_machine_pwm_duty_set(machine_pwm_obj_t *self, mp_int_t duty);

// Which channel has which GPIO pin assigned?
// (-1 if not assigned)
STATIC int chan_gpio[LEDC_CHANNEL_MAX];

// Params for PW operation
// 5khz
#define PWFREQ (5000)
// High speed mode
#if CONFIG_IDF_TARGET_ESP32
#define PWMODE (LEDC_HIGH_SPEED_MODE)
#else
#define PWMODE (LEDC_LOW_SPEED_MODE)
#endif
// 10-bit resolution (compatible with esp8266 PWM)
#define PWRES (LEDC_TIMER_10_BIT)

// Config of timer upon which we run all PWM'ed GPIO pins
STATIC bool pwm_inited = false;

// Which channel has which timer assigned?
// (-1 if not assigned)
STATIC int chan_timer[LEDC_CHANNEL_MAX];

// List of timer configs
STATIC ledc_timer_config_t timers[LEDC_TIMER_MAX];


STATIC void pwm_init(void) {

    // Initial condition: no channels assigned
    for (int x = 0; x < LEDC_CHANNEL_MAX; ++x) {
        chan_gpio[x] = -1;
        chan_timer[x] = -1;
    }

    // Initial condition: no timers assigned
    for (int x = 0; x < LEDC_TIMER_MAX; ++x) {
        timers[x].duty_resolution = PWRES;
        // unset timer is -1
        timers[x].freq_hz = -1;
        timers[x].speed_mode = PWMODE;
        timers[x].timer_num = x;
    }
}

STATIC int set_freq(int newval, ledc_timer_config_t *timer) {
    int ores = timer->duty_resolution;
    int oval = timer->freq_hz;

    // If already set, do nothing
    if (newval == oval) {
        return 1;
    }

    // Find the highest bit resolution for the requested frequency
    if (newval <= 0) {
        newval = 1;
    }
    unsigned int res = 0;
    for (unsigned int i = LEDC_APB_CLK_HZ / newval; i > 1; i >>= 1, ++res) {
    }
    if (res == 0) {
        res = 1;
    } else if (res > PWRES) {
        // Limit resolution to PWRES to match units of our duty
        res = PWRES;
    }

    // Configure the new resolution and frequency
    timer->duty_resolution = res;
    timer->freq_hz = newval;
    if (ledc_timer_config(timer) != ESP_OK) {
        timer->duty_resolution = ores;
        timer->freq_hz = oval;
        return 0;
    }
    return 1;
}

STATIC int found_timer(int freq, bool same_freq_only) {
    int free_timer_found = -1;
    int timer;
    // Find a free PWM Timer using the same freq
    for (timer = 0; timer < LEDC_TIMER_MAX; ++timer) {
        if (timers[timer].freq_hz == freq) {
            // A timer already uses the same freq. Use it now.
            return timer;
        }
        if (!same_freq_only && (free_timer_found == -1) && (timers[timer].freq_hz == -1)) {
            free_timer_found = timer;
            // Continue to check if a channel with the same freq is in use.
        }
    }

    return free_timer_found;
}

// Return true if the timer is in use in addition to current channel
STATIC bool is_timer_in_use(int current_channel, int timer) {
    int i;
    for (i = 0; i < LEDC_CHANNEL_MAX; ++i) {
        if (i != current_channel && chan_timer[i] == timer) {
            return true;
        }
    }

    return false;
}

/******************************************************************************/
// MicroPython bindings for PWM

typedef struct _machine_pwm_obj_t {
    mp_obj_base_t base;
    gpio_num_t pin;
    uint8_t active;
    uint8_t channel;
} machine_pwm_obj_t;

STATIC void mp_machine_pwm_print(const mp_print_t *print, mp_obj_t self_in, mp_print_kind_t kind) {
    machine_pwm_obj_t *self = MP_OBJ_TO_PTR(self_in);
    mp_printf(print, "PWM(%u", self->pin);
    if (self->active) {
        mp_printf(print, ", freq=%u(%u), duty=%u, resolution=%u", timers[chan_timer[self->channel]].freq_hz,
            ledc_get_freq(PWMODE, self->channel),
            mp_machine_pwm_duty_get(self), 1 << timers[chan_timer[self->channel]].duty_resolution);
    }
    mp_printf(print, ")");
}

STATIC void mp_machine_pwm_init_helper(machine_pwm_obj_t *self,
    size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_freq, ARG_duty };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_freq, MP_ARG_INT, {.u_int = -1} },
        { MP_QSTR_duty, MP_ARG_INT, {.u_int = -1} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args,
        MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    int channel;
    int avail = -1;

    // Find a free PWM channel, also spot if our pin is
    //  already mentioned.
    for (channel = 0; channel < LEDC_CHANNEL_MAX; ++channel) {
        if (chan_gpio[channel] == self->pin) {
            break;
        }
        if ((avail == -1) && (chan_gpio[channel] == -1)) {
            avail = channel;
        }
    }
    if (channel >= LEDC_CHANNEL_MAX) {
        if (avail == -1) {
            mp_raise_ValueError(MP_ERROR_TEXT("out of PWM channels"));
        }
        channel = avail;
    }
    self->channel = channel;

    int freq = args[ARG_freq].u_int;

    // Check if freq wasn't passed as an argument
    if (freq == -1) {
        // Check if already set, otherwise use the default freq
        freq = chan_timer[self->channel] != -1 ? timers[chan_timer[self->channel]].freq_hz : PWFREQ;
    }

    int timer = found_timer(freq, false);
    ESP_LOGI("1 timer %d", "timer");
    if (timer == -1) {
        mp_raise_ValueError(MP_ERROR_TEXT("1 out of PWM timers"));
    }
    chan_timer[channel] = timer;

    // New PWM assignment
    self->active = 1;
    if (chan_gpio[channel] == -1) {
        ledc_channel_config_t cfg = {
            .channel = channel,
            .duty = (1 << timers[timer].duty_resolution) / 2,
            .gpio_num = self->pin,
            .intr_type = LEDC_INTR_DISABLE,
            .speed_mode = PWMODE,
            .timer_sel = timer,
        };
        if (ledc_channel_config(&cfg) != ESP_OK) {
            mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("PWM not supported on pin %d"), self->pin);
        }
        chan_gpio[channel] = self->pin;
    }

    // Set timer frequency
    if (!set_freq(freq, &timers[timer])) {
        mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("bad frequency %d"), freq);
    }

    // Set duty cycle?
    int dval = args[ARG_duty].u_int;
    if (dval != -1) {
        mp_machine_pwm_duty_set(self, dval);
    }
}

STATIC mp_obj_t mp_machine_pwm_make_new(const mp_obj_type_t *type,
    size_t n_args, size_t n_kw, const mp_obj_t *args) {
    mp_arg_check_num(n_args, n_kw, 1, MP_OBJ_FUN_ARGS_MAX, true);
    gpio_num_t pin_id = machine_pin_get_id(args[0]);

    // create PWM object from the given pin
    machine_pwm_obj_t *self = m_new_obj(machine_pwm_obj_t);
    self->base.type = &machine_pwm_type;
    self->pin = pin_id;
    self->active = 0;
    self->channel = -1;

    // start the PWM subsystem if it's not already running
    if (!pwm_inited) {
        pwm_init();
        pwm_inited = true;
    }

    // start the PWM running for this channel
    mp_map_t kw_args;
    mp_map_init_fixed_table(&kw_args, n_kw, args + n_args);
    mp_machine_pwm_init_helper(self, n_args - 1, args + 1, &kw_args);

    return MP_OBJ_FROM_PTR(self);
}

STATIC void mp_machine_pwm_deinit(machine_pwm_obj_t *self) {
    int chan = self->channel;

    // Valid channel?
    if ((chan >= 0) && (chan < LEDC_CHANNEL_MAX)) {
        // Clean up timer if necessary
        if (!is_timer_in_use(chan, chan_timer[chan])) {
            ledc_timer_rst(PWMODE, chan_timer[chan]);
            // Flag it unused
            timers[chan_timer[chan]].freq_hz = -1;
        }

        // Mark it unused, and tell the hardware to stop routing
        chan_gpio[chan] = -1;
        chan_timer[chan] = -1;
        ledc_stop(PWMODE, chan, 0);
        self->active = 0;
        self->channel = -1;
        gpio_matrix_out(self->pin, SIG_GPIO_OUT_IDX, false, false);
    }
}

STATIC mp_obj_t mp_machine_pwm_freq_get(machine_pwm_obj_t *self) {
    return MP_OBJ_NEW_SMALL_INT(timers[chan_timer[self->channel]].freq_hz);
}

//STATIC void mp_machine_pwm_freq_set(size_t n_args, const mp_obj_t *args) {
STATIC void mp_machine_pwm_freq_set(machine_pwm_obj_t *self, mp_int_t freq) {
    if (freq == timers[chan_timer[self->channel]].freq_hz) {
        return;
    }

    int current_timer = chan_timer[self->channel];
    int new_timer = -1;
    bool current_in_use = is_timer_in_use(self->channel, current_timer);

    // Check if an already running timer with the same freq is running
    new_timer = found_timer(freq, true);

    // If no existing timer was found, and the current one is in use, then find a new one
    if (new_timer == -1 && current_in_use) {
        // Have to find a new timer
        new_timer = found_timer(freq, false);

        if (new_timer == -1) {
            mp_raise_ValueError(MP_ERROR_TEXT("2 out of PWM timers"));
        }
    }

    if (new_timer != -1 && new_timer != current_timer) {
        // Bind the channel to the new timer
        chan_timer[self->channel] = new_timer;

        if (ledc_bind_channel_timer(PWMODE, self->channel, new_timer) != ESP_OK) {
            mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("Failed to bind timer to channel"));
        }

        if (!current_in_use) {
            // Free the old timer
            ledc_timer_rst(PWMODE, current_timer);
            // Flag it unused
            timers[current_timer].freq_hz = -1;
        }

        current_timer = new_timer;
    }

    // Set the freq
    if (!set_freq(freq, &timers[current_timer])) {
        mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("bad frequency %d"), freq);
    }
}

STATIC mp_obj_t mp_machine_pwm_duty_get(machine_pwm_obj_t *self) {
    int duty = ledc_get_duty(PWMODE, self->channel);
    duty <<= PWRES - timers[chan_timer[self->channel]].duty_resolution;
    return MP_OBJ_NEW_SMALL_INT(duty);
}

STATIC void mp_machine_pwm_duty_set(machine_pwm_obj_t *self, mp_int_t duty) {
    duty &= ((1 << PWRES) - 1);
    duty >>= PWRES - timers[chan_timer[self->channel]].duty_resolution;
    check_esp_err(ledc_set_duty(PWMODE, self->channel, duty));
    check_esp_err(ledc_update_duty(PWMODE, self->channel));
}
