/*
 * This file is part of the MicroPython project, http://micropython.org/
 *
 * The MIT License (MIT)
 *
 * Copyright (c) 2013-2016 Damien P. George
 * Copyright (c) 2016 Paul Sokolovsky
 * Copyright (c) 2020 Ihor Nehrutsa
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

#include "py/mpconfig.h"
#if MICROPY_PY_UTIME64_MP_HAL

// #include <string.h>

#include "py/obj.h"
#include "py/mphal.h"
#include "py/smallint.h"
#include "py/runtime.h"
#include "extmod/utime64_mphal.h"

STATIC mp_obj_t utime64_ticks_ms(void) {
    return mp_obj_new_int_from_ull(mp_hal_ticks_ms64() & (MICROPY_PY_UTIME64_TICKS_PERIOD - 1));
}
MP_DEFINE_CONST_FUN_OBJ_0(mp_utime64_ticks_ms_obj, utime64_ticks_ms);

STATIC mp_obj_t utime64_ticks_us(void) {
    return mp_obj_new_int_from_ull(mp_hal_ticks_us64() & (MICROPY_PY_UTIME64_TICKS_PERIOD - 1));
}
MP_DEFINE_CONST_FUN_OBJ_0(mp_utime64_ticks_us_obj, utime64_ticks_us);

STATIC mp_obj_t utime64_ticks_cpu(void) {
    return mp_obj_new_int_from_ull(mp_hal_ticks_cpu64() & (MICROPY_PY_UTIME_TICKS_PERIOD - 1)); // uint64 as uint32
}
MP_DEFINE_CONST_FUN_OBJ_0(mp_utime64_ticks_cpu_obj, utime64_ticks_cpu);

STATIC mp_obj_t utime64_ticks_diff(mp_obj_t end_in, mp_obj_t start_in) {
    // we assume that the arguments come from ticks_xx so are long ints
    uint64_t start = mp_obj_get_int(start_in);
    uint64_t end = mp_obj_get_int(end_in);
    // Optimized formula avoiding if conditions. We adjust difference "forward",
    // wrap it around and adjust back.
    int64_t diff = ((end - start + MICROPY_PY_UTIME64_TICKS_PERIOD / 2) & (MICROPY_PY_UTIME64_TICKS_PERIOD - 1)) // end - start; //
        - MICROPY_PY_UTIME64_TICKS_PERIOD / 2;
    return mp_obj_new_int_from_ll(diff);
}
MP_DEFINE_CONST_FUN_OBJ_2(mp_utime64_ticks_diff_obj, utime64_ticks_diff);

STATIC mp_obj_t utime64_ticks_add(mp_obj_t ticks_in, mp_obj_t delta_in) {
    // we assume that first argument come from ticks_xx so is long int
    uint64_t ticks = mp_obj_get_int(ticks_in);
    uint64_t delta = mp_obj_get_int(delta_in);
    return mp_obj_new_int_from_ull((ticks + delta) & (MICROPY_PY_UTIME64_TICKS_PERIOD - 1)); //  & (MICROPY_PY_UTIME64_TICKS_PERIOD - 1)
}
MP_DEFINE_CONST_FUN_OBJ_2(mp_utime64_ticks_add_obj, utime64_ticks_add);

#endif // MICROPY_PY_UTIME64_MP_HAL
