// This file was developed using uStubby.
// https://github.com/pazzarpj/micropython-ustubby

/*
https://x-io.co.uk/open-source-imu-and-ahrs-algorithms/
Open source IMU and AHRS algorithms


https://habr.com/ru/post/255661/
тХКЭРП лЮДФБХЙЮ      Madgwick
яЛ. Б НАЯСФДЕМХХ:    See in discussion:
йЮЙ ЕЯРЭ             How is
йЮЙ ДНКФМН АШРЭ      How must be


https://diydrones.com/forum/topics/madgwick-imu-ahrs-and-fast-inverse-square-root?id=705844%3ATopic%3A1018435&page=4
Madgwick IMU/AHRS and Fast Inverse Square Root
Fixes is here


http://en.wikipedia.org/wiki/Fast_inverse_square_root
Fast inverse square-root


https://www.researchgate.net/publication/335235981_A_Modification_of_the_Fast_Inverse_Square_Root_Algorithm
A Modification of the Fast Inverse SquareRoot Algorithm


https://pizer.wordpress.com/2008/10/12/fast-inverse-square-root/
Fast Inverse Square Root
Pizer's Weblog
*/

// Include required definitions first.
#include "py/obj.h"
#include "py/runtime.h"
#include "py/builtin.h"

// ---------------------------------------------------------------------------------------------------
// Header files

#include <math.h>
#include "../invsqrt/invsqrt.h"

// ---------------------------------------------------------------------------------------------------
// Definitions

// #define sampleFreq  512.0f // sample frequency in Hz
#define twoKpDef    (2.0f * 0.5f)   // 2 * proportional gain
#define twoKiDef    (2.0f * 0.0f)   // 2 * integral gain

// ---------------------------------------------------------------------------------------------------
// Variable definitions

static volatile mp_float_t twoKp = twoKpDef;                                            // 2 * proportional gain (Kp)
static volatile mp_float_t twoKi = twoKiDef;                                            // 2 * integral gain (Ki)
static volatile mp_float_t q0 = 1.0f, q1 = 0.0f, q2 = 0.0f, q3 = 0.0f;                  // quaternion of sensor frame relative to auxiliary frame
static volatile mp_float_t integralFBx = 0.0f,  integralFBy = 0.0f, integralFBz = 0.0f; // integral error terms scaled by Ki

// ---------------------------------------------------------------------------------------------------
// Function declarations
STATIC mp_obj_t mahony_MahonyAHRSupdateIMU(size_t n_args, const mp_obj_t *args);

// ---------------------------------------------------------------------------------------------------
// Attitude and heading reference system (AHRS) algorithm update
//
// def MahonyAHRSupdate(gx : float, gy : float, gz : float, ax : float, ay : float, az : float, mx : float, my : float, mz : float, delta_t_us:int) -> None:
//
STATIC mp_obj_t mahony_MahonyAHRSupdate(size_t n_args, const mp_obj_t *args) {
    mp_float_t gx = mp_obj_get_float(args[0]);
    mp_float_t gy = mp_obj_get_float(args[1]);
    mp_float_t gz = mp_obj_get_float(args[2]);
    mp_float_t ax = mp_obj_get_float(args[3]);
    mp_float_t ay = mp_obj_get_float(args[4]);
    mp_float_t az = mp_obj_get_float(args[5]);
    mp_float_t mx = mp_obj_get_float(args[6]);
    mp_float_t my = mp_obj_get_float(args[7]);
    mp_float_t mz = mp_obj_get_float(args[8]);
    mp_int_t delta_t_us = mp_obj_get_int(args[9]);

    mp_float_t delta_t_s = 0.000001f * delta_t_us;

    mp_float_t recipNorm;
    mp_float_t q0q0, q0q1, q0q2, q0q3, q1q1, q1q2, q1q3, q2q2, q2q3, q3q3;
    mp_float_t hx, hy, bx, bz;
    mp_float_t halfvx, halfvy, halfvz, halfwx, halfwy, halfwz;
    mp_float_t halfex, halfey, halfez;
    mp_float_t qa, qb, qc;

    // Use IMU algorithm if magnetometer measurement invalid (avoids NaN in magnetometer normalisation)
    if ((mx == 0.0f) && (my == 0.0f) && (mz == 0.0f)) {
        return mahony_MahonyAHRSupdateIMU(6, args);
    }

    // Compute feedback only if accelerometer measurement valid (avoids NaN in accelerometer normalisation)
    if (!((ax == 0.0f) && (ay == 0.0f) && (az == 0.0f))) {

        // Normalise accelerometer measurement
        recipNorm = invSqrt(ax * ax + ay * ay + az * az);
        ax *= recipNorm;
        ay *= recipNorm;
        az *= recipNorm;

        // Normalise magnetometer measurement
        recipNorm = invSqrt(mx * mx + my * my + mz * mz);
        mx *= recipNorm;
        my *= recipNorm;
        mz *= recipNorm;

        // Auxiliary variables to avoid repeated arithmetic
        q0q0 = q0 * q0;
        q0q1 = q0 * q1;
        q0q2 = q0 * q2;
        q0q3 = q0 * q3;
        q1q1 = q1 * q1;
        q1q2 = q1 * q2;
        q1q3 = q1 * q3;
        q2q2 = q2 * q2;
        q2q3 = q2 * q3;
        q3q3 = q3 * q3;

        // Reference direction of Earth's magnetic field
        hx = 2.0f * (mx * (0.5f - q2q2 - q3q3) + my * (q1q2 - q0q3) + mz * (q1q3 + q0q2));
        hy = 2.0f * (mx * (q1q2 + q0q3) + my * (0.5f - q1q1 - q3q3) + mz * (q2q3 - q0q1));
        bx = sqrt(hx * hx + hy * hy);
        bz = 2.0f * (mx * (q1q3 - q0q2) + my * (q2q3 + q0q1) + mz * (0.5f - q1q1 - q2q2));

        // Estimated direction of gravity and magnetic field
        halfvx = q1q3 - q0q2;
        halfvy = q0q1 + q2q3;
        halfvz = q0q0 - 0.5f + q3q3;
        halfwx = bx * (0.5f - q2q2 - q3q3) + bz * (q1q3 - q0q2);
        halfwy = bx * (q1q2 - q0q3) + bz * (q0q1 + q2q3);
        halfwz = bx * (q0q2 + q1q3) + bz * (0.5f - q1q1 - q2q2);

        // Error is sum of cross product between estimated direction and measured direction of field vectors
        halfex = (ay * halfvz - az * halfvy) + (my * halfwz - mz * halfwy);
        halfey = (az * halfvx - ax * halfvz) + (mz * halfwx - mx * halfwz);
        halfez = (ax * halfvy - ay * halfvx) + (mx * halfwy - my * halfwx);

        // Compute and apply integral feedback if enabled
        if (twoKi > 0.0f) {
            integralFBx += twoKi * halfex * delta_t_s;    // integral error scaled by Ki
            integralFBy += twoKi * halfey * delta_t_s;
            integralFBz += twoKi * halfez * delta_t_s;
            gx += integralFBx;  // apply integral feedback
            gy += integralFBy;
            gz += integralFBz;
        } else {
            integralFBx = 0.0f; // prevent integral windup
            integralFBy = 0.0f;
            integralFBz = 0.0f;
        }

        // Apply proportional feedback
        gx += twoKp * halfex;
        gy += twoKp * halfey;
        gz += twoKp * halfez;
    }

    // Integrate rate of change of quaternion
    gx *= (0.5f * delta_t_s);     // pre-multiply common factors
    gy *= (0.5f * delta_t_s);
    gz *= (0.5f * delta_t_s);
    qa = q0;
    qb = q1;
    qc = q2;
    q0 += (-qb * gx - qc * gy - q3 * gz);
    q1 += (qa * gx + qc * gz - q3 * gy);
    q2 += (qa * gy - qb * gz + q3 * gx);
    q3 += (qa * gz + qb * gy - qc * gx);

    // Normalise quaternion
    recipNorm = invSqrt(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3);
    q0 *= recipNorm;
    q1 *= recipNorm;
    q2 *= recipNorm;
    q3 *= recipNorm;
    /*
    return mp_const_none;
    */
    // signature: mp_obj_t mp_obj_new_tuple(size_t n, const mp_obj_t *items);
    mp_obj_t ret_val[] = {
        mp_obj_new_float(q0),
        mp_obj_new_float(q1),
        mp_obj_new_float(q2),
        mp_obj_new_float(q3),
    };
    return mp_obj_new_tuple(4, ret_val);
}
MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(mahony_MahonyAHRSupdate_obj, 10, 10, mahony_MahonyAHRSupdate);

// ---------------------------------------------------------------------------------------------------
// Inertial measurement unit (IMU) algorithm update
//
// def MahonyAHRSupdateIMU(gx : float, gy : float, gz : float, ax : float, ay : float, az : float, delta_t_us:int) -> None:
//
STATIC mp_obj_t mahony_MahonyAHRSupdateIMU(size_t n_args, const mp_obj_t *args) {
    mp_float_t gx = mp_obj_get_float(args[0]);
    mp_float_t gy = mp_obj_get_float(args[1]);
    mp_float_t gz = mp_obj_get_float(args[2]);
    mp_float_t ax = mp_obj_get_float(args[3]);
    mp_float_t ay = mp_obj_get_float(args[4]);
    mp_float_t az = mp_obj_get_float(args[5]);
    mp_int_t delta_t_us = mp_obj_get_int(args[6]);

    mp_float_t delta_t_s = 0.000001f * delta_t_us;

    mp_float_t recipNorm;
    mp_float_t halfvx, halfvy, halfvz;
    mp_float_t halfex, halfey, halfez;
    mp_float_t qa, qb, qc;

    // Compute feedback only if accelerometer measurement valid (avoids NaN in accelerometer normalisation)
    if (!((ax == 0.0f) && (ay == 0.0f) && (az == 0.0f))) {

        // Normalise accelerometer measurement
        recipNorm = invSqrt(ax * ax + ay * ay + az * az);
        ax *= recipNorm;
        ay *= recipNorm;
        az *= recipNorm;

        // Estimated direction of gravity and vector perpendicular to magnetic flux
        halfvx = q1 * q3 - q0 * q2;
        halfvy = q0 * q1 + q2 * q3;
        halfvz = q0 * q0 - 0.5f + q3 * q3;

        // Error is sum of cross product between estimated and measured direction of gravity
        halfex = (ay * halfvz - az * halfvy);
        halfey = (az * halfvx - ax * halfvz);
        halfez = (ax * halfvy - ay * halfvx);

        // Compute and apply integral feedback if enabled
        if (twoKi > 0.0f) {
            integralFBx += twoKi * halfex * delta_t_s;    // integral error scaled by Ki
            integralFBy += twoKi * halfey * delta_t_s;
            integralFBz += twoKi * halfez * delta_t_s;
            gx += integralFBx;  // apply integral feedback
            gy += integralFBy;
            gz += integralFBz;
        } else {
            integralFBx = 0.0f; // prevent integral windup
            integralFBy = 0.0f;
            integralFBz = 0.0f;
        }

        // Apply proportional feedback
        gx += twoKp * halfex;
        gy += twoKp * halfey;
        gz += twoKp * halfez;
    }

    // Integrate rate of change of quaternion
    gx *= (0.5f * delta_t_s);     // pre-multiply common factors
    gy *= (0.5f * delta_t_s);
    gz *= (0.5f * delta_t_s);
    qa = q0;
    qb = q1;
    qc = q2;
    q0 += (-qb * gx - qc * gy - q3 * gz);
    q1 += (qa * gx + qc * gz - q3 * gy);
    q2 += (qa * gy - qb * gz + q3 * gx);
    q3 += (qa * gz + qb * gy - qc * gx);

    // Normalise quaternion
    recipNorm = invSqrt(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3);
    q0 *= recipNorm;
    q1 *= recipNorm;
    q2 *= recipNorm;
    q3 *= recipNorm;
    /*
    return mp_const_none;
    */
    // signature: mp_obj_t mp_obj_new_tuple(size_t n, const mp_obj_t *items);
    mp_obj_t ret_val[] = {
        mp_obj_new_float(q0),
        mp_obj_new_float(q1),
        mp_obj_new_float(q2),
        mp_obj_new_float(q3),
    };
    return mp_obj_new_tuple(4, ret_val);
}
MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(mahony_MahonyAHRSupdateIMU_obj, 7, 7, mahony_MahonyAHRSupdateIMU);

// https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles
#define ROLL mp_float_t roll = atan2(q0 * q1 + q2 * q3, 0.5f - q1 * q1 - q2 * q2) * 57.295779513f; // degrees
#define PITCH mp_float_t pitch = asin(2.0f * (q0 * q2 - q3 * q1)) * 57.295779513f; // degrees
#define YAW mp_float_t yaw = atan2(q0 * q3 + q1 * q2, 0.5f - q2 * q2 - q3 * q3) * 57.295779513f;  // degrees
//
// def angles()
//
STATIC mp_obj_t mahony_angles() {
    // roll(X), pitch(Y), yaw(Z)
    ROLL;
    PITCH;
    YAW;

    // signature: mp_obj_t mp_obj_new_tuple(size_t n, const mp_obj_t *items);
    mp_obj_t ret_val[] = {
        mp_obj_new_float(roll),
        mp_obj_new_float(pitch),
        mp_obj_new_float(yaw),
    };
    return mp_obj_new_tuple(3, ret_val);
}
MP_DEFINE_CONST_FUN_OBJ_0(mahony_angles_obj, mahony_angles);

STATIC mp_obj_t mahony_roll() {
    ROLL;
    return mp_obj_new_float(roll);
}
MP_DEFINE_CONST_FUN_OBJ_0(mahony_roll_obj, mahony_roll);

STATIC mp_obj_t mahony_pitch() {
    PITCH;
    return mp_obj_new_float(pitch);
}
MP_DEFINE_CONST_FUN_OBJ_0(mahony_pitch_obj, mahony_pitch);

STATIC mp_obj_t mahony_yaw() {
    YAW;
    return mp_obj_new_float(yaw);
}
MP_DEFINE_CONST_FUN_OBJ_0(mahony_yaw_obj, mahony_yaw);

STATIC mp_obj_t quaternion_to_angles(size_t n_args, const mp_obj_t *args) {
    mp_arg_check_num(n_args, 0, 2, 2, false);
    mp_float_t q0 = mp_obj_get_float(args[0]);
    mp_float_t q1 = mp_obj_get_float(args[1]);
    mp_float_t q2 = mp_obj_get_float(args[2]);
    mp_float_t q3 = mp_obj_get_float(args[3]);

    // roll(X), pitch(Y), yaw(Z)
    ROLL;
    PITCH;
    YAW;

    // signature: mp_obj_t mp_obj_new_tuple(size_t n, const mp_obj_t *items);
    mp_obj_t ret_val[] = {
        mp_obj_new_float(roll),
        mp_obj_new_float(pitch),
        mp_obj_new_float(yaw),
    };
    return mp_obj_new_tuple(3, ret_val);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(quaternion_to_angles_obj, 4, 4, quaternion_to_angles);

STATIC mp_obj_t angles_to_quaternion(mp_obj_t _roll, mp_obj_t _pitch, mp_obj_t _yaw) {
    // roll(X), pitch(Y), yaw(Z)
    mp_float_t roll = mp_obj_get_float(_roll) / 57.295779513f;
    mp_float_t pitch = mp_obj_get_float(_pitch) / 57.295779513f;
    mp_float_t yaw = mp_obj_get_float(_yaw) / 57.295779513f;

    // Abbreviations for the various angular functions
    mp_float_t cy = cos(yaw * 0.5);
    mp_float_t sy = sin(yaw * 0.5);
    mp_float_t cp = cos(pitch * 0.5);
    mp_float_t sp = sin(pitch * 0.5);
    mp_float_t cr = cos(roll * 0.5);
    mp_float_t sr = sin(roll * 0.5);

    mp_float_t q0 = cr * cp * cy + sr * sp * sy; // w
    mp_float_t q1 = sr * cp * cy - cr * sp * sy; // x
    mp_float_t q2 = cr * sp * cy + sr * cp * sy; // y
    mp_float_t q3 = cr * cp * sy - sr * sp * cy; // z

    // signature: mp_obj_t mp_obj_new_tuple(size_t n, const mp_obj_t *items);
    mp_obj_t ret_val[] = {
        mp_obj_new_float(q0),
        mp_obj_new_float(q1),
        mp_obj_new_float(q2),
        mp_obj_new_float(q3),
    };
    return mp_obj_new_tuple(4, ret_val);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_3(angles_to_quaternion_obj, angles_to_quaternion);

// ---------------------------------------------------------------------------------------------------
//
// def get_twoKp() -> float:
//
STATIC mp_obj_t mahony_get_twoKp() {
    mp_float_t ret_val;

    ret_val = twoKp;

    return mp_obj_new_float(ret_val);
}
MP_DEFINE_CONST_FUN_OBJ_0(mahony_get_twoKp_obj, mahony_get_twoKp);

//
// def get_twoKi() -> float:
//
STATIC mp_obj_t mahony_get_twoKi() {
    mp_float_t ret_val;

    ret_val = twoKi;

    return mp_obj_new_float(ret_val);
}
MP_DEFINE_CONST_FUN_OBJ_0(mahony_get_twoKi_obj, mahony_get_twoKi);

//
// def set_twoKi(twoKi : float) -> None:
//
STATIC mp_obj_t mahony_set_twoKi(mp_obj_t twoKi_obj) {
    mp_float_t _twoKi = mp_obj_get_float(twoKi_obj);

    twoKi = _twoKi;

    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_1(mahony_set_twoKi_obj, mahony_set_twoKi);

//
// def set_twoKp(twoKp : float) -> None:
//
STATIC mp_obj_t mahony_set_twoKp(mp_obj_t twoKp_obj) {
    mp_float_t _twoKp = mp_obj_get_float(twoKp_obj);

    twoKp = _twoKp;

    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_1(mahony_set_twoKp_obj, mahony_set_twoKp);

STATIC const mp_rom_map_elem_t mahony_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_mahony) },
    { MP_ROM_QSTR(MP_QSTR_MahonyAHRSupdate), MP_ROM_PTR(&mahony_MahonyAHRSupdate_obj) },
    { MP_ROM_QSTR(MP_QSTR_MahonyAHRSupdateIMU), MP_ROM_PTR(&mahony_MahonyAHRSupdateIMU_obj) },
    { MP_ROM_QSTR(MP_QSTR_Mahony_angles), MP_ROM_PTR(&mahony_angles_obj) },
    { MP_ROM_QSTR(MP_QSTR_Mahony_roll), MP_ROM_PTR(&mahony_roll_obj) },
    { MP_ROM_QSTR(MP_QSTR_Mahony_pitch), MP_ROM_PTR(&mahony_pitch_obj) },
    { MP_ROM_QSTR(MP_QSTR_Mahony_yaw), MP_ROM_PTR(&mahony_yaw_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_twoKp), MP_ROM_PTR(&mahony_get_twoKp_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_twoKi), MP_ROM_PTR(&mahony_get_twoKi_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_twoKi), MP_ROM_PTR(&mahony_set_twoKi_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_twoKp), MP_ROM_PTR(&mahony_set_twoKp_obj) },
    { MP_ROM_QSTR(MP_QSTR_angles_to_quaternion), MP_ROM_PTR(&angles_to_quaternion_obj) },
    { MP_ROM_QSTR(MP_QSTR_quaternion_to_angles), MP_ROM_PTR(&quaternion_to_angles_obj) },
};

STATIC MP_DEFINE_CONST_DICT(mahony_module_globals, mahony_module_globals_table);
const mp_obj_module_t mahony_user_cmodule = {
    .base = {&mp_type_module},
    .globals = (mp_obj_dict_t *)&mahony_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_mahony, mahony_user_cmodule);
