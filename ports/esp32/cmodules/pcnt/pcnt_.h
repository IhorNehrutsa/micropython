#pragma once

#include <driver/gpio.h>
#include "driver/pcnt.h"

#define _INT16_MAX (32766)
#define _INT16_MIN (-32766)

enum puType {
    NONE,
    DOWN,
    UP
};

enum encType {
    SINGLE,
    HALF,
    FULL
};

typedef struct _pcnt_PCNT_obj_t {
    mp_obj_base_t base;
    gpio_num_t aPinNumber;
    gpio_num_t bPinNumber;
    enum puType useInternalWeakPullResistors;

    pcnt_config_t r_enc_config;
    bool attached; 
    pcnt_unit_t unit;
    volatile int64_t count; 

    bool fullQuad; // for QUAD() only
} pcnt_PCNT_obj_t;

extern const pcnt_PCNT_obj_t *pcnts[PCNT_UNIT_MAX];// = { NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL };

extern int machine_pin_get_gpio(mp_obj_t pin_in);

#pragma once
