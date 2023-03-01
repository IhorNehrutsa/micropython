/*
 * This file is part of the MicroPython project, http://micropython.org/
 *
 * The MIT License (MIT)
 *
 * Copyright (c) 2016-2021 Damien P. George
 * Copyright (c) 2018 Alan Dragomirecky
 * Copyright (c) 2020 Antoine Aubert
 * Copyright (c) 2021, 2023 Ihor Nehrutsa
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

#include <math.h>

#include "py/runtime.h"
#include "py/mphal.h"

#include "driver/ledc.h"
#include "esp_err.h"

#include "py/mpprint.h"
//#define PWM_DBG(...)
#define PWM_DBG(...) mp_printf(MP_PYTHON_PRINTER, __VA_ARGS__); mp_printf(&mp_plat_print, "\n");
#define MP_PRN_LEVEL 1000

// Total number of channels
#define PWM_CHANNEL_MAX (LEDC_SPEED_MODE_MAX * LEDC_CHANNEL_MAX)

typedef struct _chan_t {
    // Which channel has which GPIO pin assigned?
    // (-1 if not assigned)
    gpio_num_t pin;
    // Which channel has which timer assigned?
    // (-1 if not assigned)
    int timer;
    uint32_t freq;
} chan_t;

// List of PWM channels
STATIC chan_t chans[LEDC_SPEED_MODE_MAX][LEDC_CHANNEL_MAX];

// Total number of timers
#define PWM_TIMER_MAX (LEDC_SPEED_MODE_MAX * LEDC_TIMER_MAX)

// List of timer configs
STATIC ledc_timer_config_t timers[LEDC_SPEED_MODE_MAX][LEDC_TIMER_MAX];

// Params for PWM operation
// 5khz is default frequency
#define PWM_FREQ (5000)

// 10-bit resolution (compatible with esp8266 PWM)
#define PWM_RES_10_BIT (LEDC_TIMER_10_BIT)

// Maximum duty value on 10-bit resolution
#define MAX_DUTY_U10 ((1 << PWM_RES_10_BIT) - 1)
// https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/ledc.html#supported-range-of-frequency-and-duty-resolutions
// duty() uses 10-bit resolution or less
// duty_u16() and duty_ns() use 16-bit resolution or less

// Possible highest resolution in device
#if (LEDC_TIMER_BIT_MAX - 1) < LEDC_TIMER_16_BIT
#define HIGHEST_PWM_RES (LEDC_TIMER_BIT_MAX - 1)
#else
#define HIGHEST_PWM_RES (LEDC_TIMER_16_BIT) // 20 bit for ESP32, but 16 bit is used
#endif
// Duty resolution of user interface in `duty_u16()` and `duty_u16` parameter in constructor/initializer
#define UI_RES_16_BIT (16)
// Maximum duty value on highest user interface resolution
#define UI_MAX_DUTY ((1 << UI_RES_16_BIT) - 1)
// How much to shift from the HIGHEST_PWM_RES duty resolution to the user interface duty resolution UI_RES_16_BIT
#define UI_RES_SHIFT (UI_RES_16_BIT - HIGHEST_PWM_RES) // 0 for ESP32, 2 for S2, S3, C3

#if SOC_LEDC_SUPPORT_REF_TICK
// If the PWM frequency is less than EMPIRIC_FREQ, then LEDC_REF_CLK_HZ(1 MHz) source is used, else LEDC_APB_CLK_HZ(80 MHz) source is used
#define EMPIRIC_FREQ (10) // Hz
#endif

// Config of timer upon which we run all PWM'ed GPIO pins
STATIC bool pwm_inited = false;

// MicroPython PWM object struct
typedef struct _machine_pwm_obj_t {
    mp_obj_base_t base;
    bool active;
    gpio_num_t pin;
    ledc_mode_t mode;
    ledc_channel_t channel;
    ledc_timer_t timer;
    int duty_x; // PWM_RES_10_BIT if duty(), HIGHEST_PWM_RES if duty_u16(), -HIGHEST_PWM_RES if duty_ns()
    int duty_u10; // stored values from previous duty setters
    int duty_u16; // - / -
    int duty_ns; // - / -
    #if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(4, 4, 0)
    uint8_t output_invert;
    #endif
} machine_pwm_obj_t;

STATIC void pwm_init(void) {
    // Initial condition: no channels assigned

    for (int m = 0; m < LEDC_SPEED_MODE_MAX; ++m) {
        for (int c = 0; c < LEDC_CHANNEL_MAX; ++c) {
            chans[m][c].pin = -1;
            chans[m][c].timer = -1;
            chans[m][c].freq = -1;
        }
    }

    // Prepare all timers config
    // Initial condition: no timers assigned
    for (int m = 0; m < LEDC_SPEED_MODE_MAX; ++m) {
        for (int t = 0; t < LEDC_TIMER_MAX; ++t) {
            timers[m][t].duty_resolution = HIGHEST_PWM_RES;
            // unset timer is -1
            timers[m][t].freq_hz = -1;
            timers[m][t].speed_mode = m;
            timers[m][t].timer_num = t;
            timers[m][t].clk_cfg = LEDC_AUTO_CLK; // will reinstall later according to the EMPIRIC_FREQ
        }
    }
}

// Returns the number of timer uses
STATIC int timer_used(int mode, int timer) {
    int count = 0;
    if (timer >= 0) {
        for (int c = 0; c < LEDC_CHANNEL_MAX; ++c) {
            if (chans[mode][c].timer == timer) {
                ++count;
            }
        }
    }
    return count;
}

// Deinit channel and timer if the timer is unused, detach pin
STATIC void pwm_deinit(int mode, int channel) {
    // Is valid channel?
    if ((mode >= 0) && (mode < LEDC_SPEED_MODE_MAX) && (channel >= 0) && (channel < LEDC_CHANNEL_MAX)) {
        // Clean up timer if necessary
        int timer = chans[mode][channel].timer;
        if (timer >= 0) {
            if (timer_used(mode, timer) == 0) {
                check_esp_err(ledc_timer_rst(mode, timer));
                // Flag it unused
                timers[mode][timer].freq_hz = -1;
            }
        }

        int pin = chans[mode][channel].pin;
        if (pin >= 0) {
            // Mark it unused, and tell the hardware to stop routing
            check_esp_err(ledc_stop(mode, channel, 0));
            // Disable ledc signal for the pin
            // gpio_matrix_out(pin, SIG_GPIO_OUT_IDX, false, false);
            if (mode == LEDC_LOW_SPEED_MODE) {
                gpio_matrix_out(pin, LEDC_LS_SIG_OUT0_IDX + channel, false, true);
            } else {
                #if LEDC_SPEED_MODE_MAX > 1
                #if CONFIG_IDF_TARGET_ESP32
                gpio_matrix_out(pin, LEDC_HS_SIG_OUT0_IDX + channel, false, true);
                #else
                #error Add supported CONFIG_IDF_TARGET_ESP32_xxx
                #endif
                #endif
            }
        }
        chans[mode][channel].pin = -1;
        chans[mode][channel].timer = -1;
        chans[mode][channel].freq = -1;
    }
}

// This called from Ctrl-D soft reboot
void machine_pwm_deinit_all(void) {
    if (pwm_inited) {
        for (int m = 0; m < LEDC_SPEED_MODE_MAX; ++m) {
            for (int c = 0; c < LEDC_CHANNEL_MAX; ++c) {
                pwm_deinit(m, c);
            }
        }
        pwm_inited = false;
    }
}

STATIC void configure_channel(machine_pwm_obj_t *self) {
    ledc_channel_config_t cfg = {
        .channel = self->channel,
        .duty = (1 << timers[self->mode][self->timer].duty_resolution) / 2,
        .gpio_num = self->pin,
        .intr_type = LEDC_INTR_DISABLE,
        .speed_mode = self->mode,
        .timer_sel = self->timer,
        #if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(4, 4, 0)
        .flags.output_invert = self->output_invert,
        #endif
    };
    PWM_DBG("aaa %d %u %d %d %d ", self->channel, (1 << (timers[self->mode][self->timer].duty_resolution)) / 2, self->pin, self->mode, self->timer);
    check_esp_err(ledc_channel_config(&cfg));
}

STATIC void pwm_is_active(machine_pwm_obj_t *self) {
    if (self->active == false) {
        mp_raise_msg(&mp_type_RuntimeError, MP_ERROR_TEXT("PWM is inactive"));
    }
}

// Calculate the duty parameters based on an ns value
STATIC int ns_to_duty(machine_pwm_obj_t *self, int ns) {
    ledc_timer_config_t timer = timers[self->mode][self->timer];
    int64_t duty = ((int64_t)ns * UI_MAX_DUTY * timer.freq_hz + 500000000LL) / 1000000000LL;
    if ((ns > 0) && (duty == 0)) {
        duty = 1;
    } else if (duty > UI_MAX_DUTY) {
        duty = UI_MAX_DUTY;
    }
    return duty;
}

STATIC int duty_to_ns(machine_pwm_obj_t *self, int duty) {
    ledc_timer_config_t timer = timers[self->mode][self->timer];
    int64_t ns = ((int64_t)duty * 1000000000LL + (int64_t)timer.freq_hz * UI_MAX_DUTY / 2) / ((int64_t)timer.freq_hz * UI_MAX_DUTY);
    return ns;
}

STATIC void set_duty_u16(machine_pwm_obj_t *self, int duty) {
    pwm_is_active(self);
    if ((duty < 0) || (duty > UI_MAX_DUTY)) {
        mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("duty_u16 must be from 0 to %d"), UI_MAX_DUTY);
    }
    ledc_timer_config_t timer = timers[self->mode][self->timer];
    int channel_duty;
    if (timer.duty_resolution <= UI_RES_16_BIT) {
        channel_duty = duty >> (UI_RES_16_BIT - timer.duty_resolution);
    } else {
        channel_duty = duty << (timer.duty_resolution - UI_RES_16_BIT);
    }
    int max_duty = (1 << timer.duty_resolution) - 1;
    if (channel_duty < 0) {
        channel_duty = 0;
    } else if (channel_duty > max_duty) {
        channel_duty = max_duty;
    }
    check_esp_err(ledc_set_duty(self->mode, self->channel, channel_duty));
    check_esp_err(ledc_update_duty(self->mode, self->channel));
    // A thread-safe version of API is ledc_set_duty_and_update

    /*
    // Bug: Sometimes duty is not set right now.
    // Not a bug. It's a feature. The duty is applied at the beginning of the next signal period.
    // Bug: It has been experimentally established that the duty is setted during 2 signal periods, but 1 period is expected.
    // See https://github.com/espressif/esp-idf/issues/7288
    if (duty != get_duty_u16(self)) {
        PWM_DBG("set_duty_u16(%u), get_duty_u16():%u, channel_duty:%d, duty_resolution:%d, freq_hz:%d", duty, get_duty_u16(self), channel_duty, timer.duty_resolution, timer.freq_hz);
        ets_delay_us(2 * 1000000 / timer.freq_hz);
        if (duty != get_duty_u16(self)) {
            PWM_DBG("set_duty_u16(%u), get_duty_u16():%u, channel_duty:%d, duty_resolution:%d, freq_hz:%d", duty, get_duty_u16(self), channel_duty, timer.duty_resolution, timer.freq_hz);
        }
    }
    */

    self->duty_x = HIGHEST_PWM_RES;
    self->duty_u16 = duty;
}

STATIC void set_duty_u10(machine_pwm_obj_t *self, int duty) {
    pwm_is_active(self);
    if ((duty < 0) || (duty > MAX_DUTY_U10)) {
        mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("duty must be from 0 to %u"), MAX_DUTY_U10);
    }
    set_duty_u16(self, duty << (UI_RES_16_BIT - PWM_RES_10_BIT));
    self->duty_x = PWM_RES_10_BIT;
    self->duty_u10 = duty;
}

STATIC void set_duty_ns(machine_pwm_obj_t *self, int ns) {
    pwm_is_active(self);
    if ((ns < 0) || (ns > duty_to_ns(self, UI_MAX_DUTY))) {
        mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("duty_ns must be from 0 to %d ns"), duty_to_ns(self, UI_MAX_DUTY));
    }
    set_duty_u16(self, ns_to_duty(self, ns));
    self->duty_x = -HIGHEST_PWM_RES;
    self->duty_ns = ns;
}

// Set timer frequency
STATIC void set_freq(machine_pwm_obj_t *self, unsigned int freq) {
    ledc_timer_config_t *timer = &timers[self->mode][self->timer];
    if (timer->freq_hz != freq) {
        // Find the highest bit resolution for the requested frequency
        unsigned int i = LEDC_APB_CLK_HZ; // 80 MHz
        #if SOC_LEDC_SUPPORT_REF_TICK
        if (freq < EMPIRIC_FREQ) {
            i = LEDC_REF_CLK_HZ; // 1 MHz
        }
        #endif

        #if ESP_IDF_VERSION < ESP_IDF_VERSION_VAL(4, 4, 0)
        // original code
        i /= freq;
        #else
        // See https://github.com/espressif/esp-idf/issues/7722
        int divider = (i + freq / 2) / freq; // rounded
        if (divider == 0) {
            divider = 1;
        }
        float f = (float)i / divider; // actual frequency
        if (f <= 1.0) {
            f = 1.0;
        }
        i = (unsigned int)roundf((float)i / f);
        #endif

        unsigned int res = 0;
        for (; i > 1; i >>= 1) {
            ++res;
        }
        if (res == 0) {
            res = 1;
        } else if (res > HIGHEST_PWM_RES) {
            // Limit resolution to HIGHEST_PWM_RES to match units of our duty
            res = HIGHEST_PWM_RES;
        }

        // Configure the new resolution and frequency
        timer->duty_resolution = res;
        timer->freq_hz = freq;
        timer->clk_cfg = LEDC_USE_APB_CLK;
        #if SOC_LEDC_SUPPORT_REF_TICK
        if (freq < EMPIRIC_FREQ) {
            timer->clk_cfg = LEDC_USE_REF_TICK;
        }
        #endif

        // Set frequency
        check_esp_err(ledc_timer_config(timer));
        // Reset the timer if low speed
        if (self->mode == LEDC_LOW_SPEED_MODE) {
            check_esp_err(ledc_timer_rst(self->mode, self->timer));
        }

        // Save the same duty cycle when frequency is changed
        if (self->duty_x == HIGHEST_PWM_RES) {
            set_duty_u16(self, self->duty_u16);
        } else if (self->duty_x == PWM_RES_10_BIT) {
            set_duty_u10(self, self->duty_u10);
        } else if (self->duty_x == -HIGHEST_PWM_RES) {
            set_duty_ns(self, self->duty_ns);
        }
    }
}

#define get_duty_raw(self) ledc_get_duty(self->mode, self->channel)

STATIC uint32_t get_duty_u16(machine_pwm_obj_t *self) {
    pwm_is_active(self);
    int resolution = timers[self->mode][self->timer].duty_resolution;
    int duty = ledc_get_duty(self->mode, self->channel);
    if (resolution <= UI_RES_16_BIT) {
        duty <<= (UI_RES_16_BIT - resolution);
    } else {
        duty >>= (resolution - UI_RES_16_BIT);
    }
    return duty;
}

STATIC uint32_t get_duty_u10(machine_pwm_obj_t *self) {
    pwm_is_active(self);
    return get_duty_u16(self) >> 6; // Scale down from 16 bit to 10 bit resolution
}

STATIC uint32_t get_duty_ns(machine_pwm_obj_t *self) {
    pwm_is_active(self);
    return duty_to_ns(self, get_duty_u16(self));
}

/******************************************************************************/

#define SAME_FREQ_ONLY (true)
#define SAME_FREQ_OR_FREE (false)
#define ANY_MODE (-1)

// Return timer with the same freq
STATIC int find_timer(int mode, unsigned int freq) {
    int timer_found = -1;
    for (int c = 0; c < LEDC_CHANNEL_MAX; ++c) {
        if (chans[mode][c].freq == freq) {
            timer_found = chans[mode][c].timer;
            break;
        }
    }
    return timer_found;
}

// Find a free PWM channel, also spot if our pin is already mentioned.
STATIC int find_channel(int mode, int pin) {
    int avail_channel = -1;
    for (int c = 0; c < LEDC_CHANNEL_MAX; ++c) {
        if (chans[mode][c].pin == pin) {
            return c;
        }
        if ((avail_channel < 0) && (chans[mode][c].pin < 0)) {
            avail_channel = c;
        }
    }
    return avail_channel;
}

/******************************************************************************/
// MicroPython bindings for PWM

STATIC void mp_machine_pwm_print(const mp_print_t *print, mp_obj_t self_in, mp_print_kind_t kind) {
    machine_pwm_obj_t *self = MP_OBJ_TO_PTR(self_in);
    mp_printf(print, "PWM(Pin(%u)", self->pin);
    if (self->active) {
        mp_printf(print, ", freq=%u", ledc_get_freq(self->mode, self->timer));

        if (self->duty_x == PWM_RES_10_BIT) {
            mp_printf(print, ", duty=%d", get_duty_u10(self));
        } else if (self->duty_x == -HIGHEST_PWM_RES) {
            mp_printf(print, ", duty_ns=%d", get_duty_ns(self));
        } else {
            mp_printf(print, ", duty_u16=%d", get_duty_u16(self));
        }
        #if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(4, 4, 0)
        if (self->output_invert) {
            mp_printf(print, ", invert=%d", self->output_invert);
        }
        #endif
        mp_printf(print, ")");
        int resolution = timers[self->mode][self->timer].duty_resolution;
        mp_printf(print, "  # resolution=%d", resolution);

        mp_printf(print, ", (duty=%.2f%%, resolution=%.3f%%)", 100.0 * get_duty_raw(self) / (1 << resolution), 100.0 * 1 / (1 << resolution)); // percents

        mp_printf(print, ", mode=%d, channel=%d, timer=%d", self->mode, self->channel, self->timer);
    } else {
        mp_printf(print, ")");
    }
}

// This called from pwm.init() method
STATIC void mp_machine_pwm_init_helper(machine_pwm_obj_t *self,
    size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_freq, ARG_duty, ARG_duty_u16, ARG_duty_ns
        #if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(4, 4, 0)
        , ARG_invert
        #endif
    };
    static const mp_arg_t allowed_args[] = {
//      { MP_QSTR_freq, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = -1} },
        { MP_QSTR_freq, MP_ARG_INT, {.u_int = -1} },
        { MP_QSTR_duty, MP_ARG_KW_ONLY | MP_ARG_INT, {.u_int = -1} },
        { MP_QSTR_duty_u16, MP_ARG_KW_ONLY | MP_ARG_INT, {.u_int = -1} },
        { MP_QSTR_duty_ns, MP_ARG_KW_ONLY | MP_ARG_INT, {.u_int = -1} },
        #if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(4, 4, 0)
        { MP_QSTR_invert, MP_ARG_KW_ONLY | MP_ARG_INT, {.u_int = 0}},
        #endif
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args,
        MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    int duty = args[ARG_duty].u_int;
    int duty_u16 = args[ARG_duty_u16].u_int;
    int duty_ns = args[ARG_duty_ns].u_int;
    if (((duty != -1) && (duty_u16 != -1)) || ((duty != -1) && (duty_ns != -1)) || ((duty_u16 != -1) && (duty_ns != -1))) {
        mp_raise_ValueError(MP_ERROR_TEXT("only one of parameters 'duty', 'duty_u16' or 'duty_ns' is allowed"));
    }
    /*
    if ((duty < 0) && (duty_u16 < 0) && (duty_ns < 0)) {
        mp_raise_ValueError(MP_ERROR_TEXT("one of parameters 'duty', 'duty_u16', or 'duty_ns' is required"));
    }
    */

    int mode = -1;
    int channel = -1;
    for (int m = 0; m < LEDC_SPEED_MODE_MAX; ++m) {
        channel = find_channel(m, self->pin);
        if (channel >= 0) {
            mode = m;
            break;
        }
    }
    if (channel < 0) {
        mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("out of PWM channels:%d"), PWM_CHANNEL_MAX); // in all modes
    }

    int freq = args[ARG_freq].u_int;
    // Check if freq wasn't passed as an argument
    if (freq < 0) {
        // Check if already set, otherwise use the default freq.
        // It is possible in case:
        // pwm = PWM(pin, freq=1000, duty=256)
        // pwm = PWM(pin, duty=128)
        if (chans[mode][channel].timer >= 0) {
            freq = timers[mode][chans[mode][channel].timer].freq_hz;
        }
        if (freq <= 0) {
            freq = PWM_FREQ;
        }
    }
    if ((freq <= 0) || (freq > 40000000)) {
        mp_raise_ValueError(MP_ERROR_TEXT("freqency must be from 1Hz to 40MHz"));
    }

    int timer_idx;
    int current_in_use = timer_used(channel, self->timer);
    PWM_DBG("www channel=%d self->timer=%d current_in_use=%d ", channel, self->timer, current_in_use);

    if ((current_in_use >= 1) && (current_in_use < (LEDC_TIMER_MAX - 1))) {
        timer_idx = find_timer(mode, freq);
    } else {
        timer_idx = chans[mode][channel].timer;
    }

    if (timer_idx < 0) {
        timer_idx = find_timer(mode, freq);
    }
    if (timer_idx < 0) {
        mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("out of PWM timers:%d"), PWM_TIMER_MAX); // in all modes
    }

    PWM_DBG("eee channel=%d mode=%d timer_idx=%d to_mode=%d ", channel, mode, timer_idx, CHANNEL_IDX_TO_MODE(channel));
    if (CHANNEL_IDX_TO_MODE(channel) != mode) {
        // unregister old channel
        chans[mode][channel].pin = -1;
        chans[mode][channel].timer = -1;
        // find new channel
        channel = find_channel(mode, self->pin);
        if (CHANNEL_IDX_TO_MODE(channel) != mode) {
            mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("out of PWM channels:%d"), PWM_CHANNEL_MAX); // in current mode
        }
        mode = CHANNEL_IDX_TO_MODE(channel);
    }
    self->mode = mode;
    self->timer = timer;
    self->channel = channel;
    PWM_DBG("qqq channel=%d %d %d %d mode=%d ", channel, timer_idx, self->channel, self->timer, self->mode);
    #if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(4, 4, 0)
    self->output_invert = args[ARG_invert].u_int == 0 ? 0 : 1;
    #endif

    // New PWM assignment
    if ((chans[mode][channel].pin < 0) || (chans[mode][channel].timer != timer_idx)) {
        configure_channel(self);
        chans[mode][channel].pin = self->pin;
    }
    chans[mode][channel].timer = timer_idx;
    self->active = true;

    set_freq(self, freq);

    // Set duty cycle?
    if (duty_u16 >= 0) {
        set_duty_u16(self, duty_u16);
    } else if (duty_ns >= 0) {
        set_duty_ns(self, duty_ns);
    } else if (duty >= 0) {
        set_duty_u10(self, duty);
    } else if (self->duty_x == 0) {
        set_duty_u10(self, (1 << PWM_RES_10_BIT) / 2); // 50%
    }
}

// This called from PWM() constructor
STATIC mp_obj_t mp_machine_pwm_make_new(const mp_obj_type_t *type,
    size_t n_args, size_t n_kw, const mp_obj_t *args) {
    mp_arg_check_num(n_args, n_kw, 1, 2, true);
    gpio_num_t pin_id = machine_pin_get_id(args[0]);

    // create PWM object from the given pin
    machine_pwm_obj_t *self = mp_obj_malloc(machine_pwm_obj_t, &machine_pwm_type);
    self->pin = pin_id;
    self->active = false;
    self->mode = -1;
    self->channel = -1;
    self->timer = -1;
    self->duty_x = 0;

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

// This called from pwm.deinit() method
STATIC void mp_machine_pwm_deinit(machine_pwm_obj_t *self) {
    pwm_deinit(self->mode, self->channel);
    self->active = false;
    self->mode = -1;
    self->channel = -1;
    self->timer = -1;
    self->duty_x = 0;
}

// Set's and get's methods of PWM class

STATIC mp_obj_t mp_machine_pwm_freq_get(machine_pwm_obj_t *self) {
    pwm_is_active(self);
    return MP_OBJ_NEW_SMALL_INT(ledc_get_freq(self->mode, self->timer));
}

STATIC void mp_machine_pwm_freq_set(machine_pwm_obj_t *self, mp_int_t freq) {
    pwm_is_active(self);
    if ((freq <= 0) || (freq > 40000000)) {
        mp_raise_ValueError(MP_ERROR_TEXT("freqency must be from 1Hz to 40MHz"));
    }
    if (freq == timers[self->mode][self->timer].freq_hz) {
        return;
    }

    int current_in_use = timer_used(self->mode, self->channel, self->timer);

    // Check if an already running timer with the same freq is running
    int new_timer = find_timer(self->mode, freq);

    // If no existing timer was found, and the current one is in use, then find a new one
    if ((new_timer < 0) && current_in_use) {
        // Have to find a new timer
        new_timer = find_timer(self->mode, freq);

        if (new_timer < 0) {
            mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("out of PWM timers:%d"), PWM_TIMER_MAX); // in current mode
        }
    }

    if ((new_timer >= 0) && (new_timer != self->timer)) {
        // Bind the channel to the new timer
        chans[self->channel].timer = new_timer;

        if (ledc_bind_channel_timer(self->mode, self->channel, new_timer) != ESP_OK) {
            mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("failed to bind timer to channel"));
        }

        if (!current_in_use) {
            // Free the old timer
            check_esp_err(ledc_timer_rst(self->mode, self->timer));
            // Flag it unused
            timers[self->timer].freq_hz = -1;
        }

        self->timer = new_timer;
    }
    self->mode = mode;
    self->timer = timer;

    set_freq(self, freq);
}

STATIC mp_obj_t mp_machine_pwm_duty_get(machine_pwm_obj_t *self) {
    return MP_OBJ_NEW_SMALL_INT(get_duty_u10(self));
}

STATIC void mp_machine_pwm_duty_set(machine_pwm_obj_t *self, mp_int_t duty) {
    set_duty_u10(self, duty);
}

STATIC mp_obj_t mp_machine_pwm_duty_get_u16(machine_pwm_obj_t *self) {
    return MP_OBJ_NEW_SMALL_INT(get_duty_u16(self));
}

STATIC void mp_machine_pwm_duty_set_u16(machine_pwm_obj_t *self, mp_int_t duty_u16) {
    set_duty_u16(self, duty_u16);
}

STATIC mp_obj_t mp_machine_pwm_duty_get_ns(machine_pwm_obj_t *self) {
    return MP_OBJ_NEW_SMALL_INT(get_duty_ns(self));
}

STATIC void mp_machine_pwm_duty_set_ns(machine_pwm_obj_t *self, mp_int_t duty_ns) {
    set_duty_ns(self, duty_ns);
}
