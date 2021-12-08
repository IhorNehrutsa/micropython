#pragma once

#include <driver/gpio.h>
#include "driver/pcnt.h"

#define _INT16_MAX (32766)
#define _INT16_MIN (-32766)

enum edgeKind {
    RISING = 0x1,
    FALLING = 0x2
};

typedef struct _mp_pcnt_obj_t {
    mp_obj_base_t base;
    gpio_num_t aPinNumber;
    gpio_num_t bPinNumber;

    pcnt_config_t r_enc_config;
    bool attached;
    pcnt_unit_t unit;
    volatile int64_t count;

    int filter;
    enum edgeKind edge; // Counter only
    int8_t x124; // Encoder only
    float scale;
} mp_pcnt_obj_t;

extern int machine_pin_get_id(mp_obj_t pin_in);

#pragma once