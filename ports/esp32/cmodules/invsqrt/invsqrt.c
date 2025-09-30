
// This file was developed using uStubby.
// https://github.com/pazzarpj/micropython-ustubby

// Include required definitions first.
#include "py/obj.h"
#include "py/runtime.h"
#include "py/builtin.h"

#include <math.h>

// function for madgwick.c and for mahony.c

// #define USE_VERSION 3

float invSqrt(float x) {
    #if USE_VERSION == 1
    // Fast inverse square-root
    // See: http://en.wikipedia.org/wiki/Fast_inverse_square_root
    float halfx = 0.5f * x;
    float y = x;
    long i = *(long *)&y;
    i = 0x5f3759df - (i >> 1);
    y = *(float *)&i;
    return y * (1.5f - (halfx * y * y));

    #elif USE_VERSION == 2
    // A Modification of the Fast Inverse SquareRoot Algorithm
    // See: https://www.researchgate.net/publication/335235981_A_Modification_of_the_Fast_Inverse_Square_Root_Algorithm
    float simhalfnumber = 0.500438180f * x;
    int i = *(int *)&x;
    i = 0x5F375A86 - (i >> 1);
    float y = *(float *)&i;
    y = y * (1.50131454f - simhalfnumber * y * y);
    return y * (1.50000086f - 0.999124984f * simhalfnumber * y * y);
    #elif USE_VERSION == 3
    // Fast Inverse Square Root. Pizer's Weblog
    // See: https://pizer.wordpress.com/2008/10/12/fast-inverse-square-root/
    uint32_t i = 0x5F1F1412 - (*(uint32_t *)&x >> 1);
    float tmp = *(float *)&i;
    return tmp * (1.69000231f - 0.714158168f * x * tmp * tmp);
    #else
    return 1.0f / sqrt(x);
    #endif
}

// functions for micropython invsqrt module

//
// 1 / sqrt(x)
//
STATIC mp_obj_t invsqrt_invSqrt(mp_obj_t x_obj) {
    mp_float_t x = mp_obj_get_float(x_obj);
    mp_float_t ret_val;

    ret_val = 1.0f / sqrt(x);

    return mp_obj_new_float(ret_val);
}
MP_DEFINE_CONST_FUN_OBJ_1(invsqrt_invSqrt_obj, invsqrt_invSqrt);


#if USE_VERSION == 1
//
// Fast inverse square-root
// http://en.wikipedia.org/wiki/Fast_inverse_square_root
//
STATIC mp_obj_t invsqrt_invSqrt1(mp_obj_t x_obj) {
    mp_float_t x = mp_obj_get_float(x_obj);
    mp_float_t ret_val;

    float halfx = 0.5f * x;
    float y = x;
    long i = *(long *)&y;
    i = 0x5f3759df - (i >> 1);
    y = *(float *)&i;
    ret_val = y * (1.5f - (halfx * y * y));

    return mp_obj_new_float(ret_val);
}
MP_DEFINE_CONST_FUN_OBJ_1(invsqrt_invSqrt1_obj, invsqrt_invSqrt1);
#endif

#if USE_VERSION == 2
//
// A Modification of the Fast Inverse SquareRoot Algorithm
// https://www.researchgate.net/publication/335235981_A_Modification_of_the_Fast_Inverse_Square_Root_Algorithm
//
STATIC mp_obj_t invsqrt_invSqrt2(mp_obj_t x_obj) {
    mp_float_t x = mp_obj_get_float(x_obj);
    mp_float_t ret_val;

    float simhalfnumber = 0.500438180f * x;
    int i = *(int *)&x;
    i = 0x5F375A86 - (i >> 1);
    float y = *(float *)&i;
    y = y * (1.50131454f - simhalfnumber * y * y);
    ret_val = y * (1.50000086f - 0.999124984f * simhalfnumber * y * y);

    return mp_obj_new_float(ret_val);
}
MP_DEFINE_CONST_FUN_OBJ_1(invsqrt_invSqrt2_obj, invsqrt_invSqrt2);
#endif

#if USE_VERSION == 3
//
// Fast Inverse Square Root. Pizer's Weblog
// https://pizer.wordpress.com/2008/10/12/fast-inverse-square-root/
//
STATIC mp_obj_t invsqrt_invSqrt3(mp_obj_t x_obj) {
    mp_float_t x = mp_obj_get_float(x_obj);
    mp_float_t ret_val;

    uint32_t i = 0x5F1F1412 - (*(uint32_t *)&x >> 1);
    float tmp = *(float *)&i;
    ret_val = tmp * (1.69000231f - 0.714158168f * x * tmp * tmp);

    return mp_obj_new_float(ret_val);
}
MP_DEFINE_CONST_FUN_OBJ_1(invsqrt_invSqrt3_obj, invsqrt_invSqrt3);
#endif

STATIC const mp_rom_map_elem_t invsqrt_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_invsqrt) },
    { MP_ROM_QSTR(MP_QSTR_invSqrt), MP_ROM_PTR(&invsqrt_invSqrt_obj) },
    #if USE_VERSION == 1
    { MP_ROM_QSTR(MP_QSTR_invSqrt1), MP_ROM_PTR(&invsqrt_invSqrt1_obj) },
    #endif
    #if USE_VERSION == 2
    { MP_ROM_QSTR(MP_QSTR_invSqrt2), MP_ROM_PTR(&invsqrt_invSqrt2_obj) },
    #endif
    #if USE_VERSION == 3
    { MP_ROM_QSTR(MP_QSTR_invSqrt3), MP_ROM_PTR(&invsqrt_invSqrt3_obj) },
    #endif
};

STATIC MP_DEFINE_CONST_DICT(invsqrt_module_globals, invsqrt_module_globals_table);
const mp_obj_module_t invsqrt_user_cmodule = {
    .base = {&mp_type_module},
    .globals = (mp_obj_dict_t *)&invsqrt_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_invsqrt, invsqrt_user_cmodule);
