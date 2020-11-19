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

//---------------------------------------------------------------------------------------------------
// Header files

#include <math.h>
#include "../invsqrt/invsqrt.h"

//---------------------------------------------------------------------------------------------------
// Definitions

//#define sampleFreq  512.0f // sample frequency in Hz
#define betaDef     0.1f        // 2 * proportional gain

//---------------------------------------------------------------------------------------------------
// Variable definitions

static volatile float beta = betaDef;                              // 2 * proportional gain (Kp)
static volatile float q0 = 1.0f, q1 = 0.0f, q2 = 0.0f, q3 = 0.0f;  // quaternion of sensor frame relative to auxiliary frame

//---------------------------------------------------------------------------------------------------
// Function declarations

//====================================================================================================
// Functions

//---------------------------------------------------------------------------------------------------
// AHRS algorithm update

//
//def MadgwickAHRSupdate(gx : float, gy : float, gz : float, ax : float, ay : float, az : float, mx : float, my : float, mz : float, delta_t_us:int) -> None:
//
STATIC mp_obj_t madgwick_MadgwickAHRSupdate(size_t n_args, const mp_obj_t *args) {
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

    float delta_t_s = 0.000001f * delta_t_us;

    float recipNorm;
    float s0, s1, s2, s3;
    float qDot1, qDot2, qDot3, qDot4;
    float hx, hy;
    float _2q0mx, _2q0my, _2q0mz, _2q1mx, _2bx, _2bz, _4bx, _4bz, _2q0, _2q1, _2q2, _2q3, _2q0q2, _2q2q3, q0q0, q0q1, q0q2, q0q3, q1q1, q1q2, q1q3, q2q2, q2q3, q3q3;

    // Use IMU algorithm if magnetometer measurement invalid (avoids NaN in magnetometer normalisation)
    if((mx == 0.0f) && (my == 0.0f) && (mz == 0.0f)) {
        // MadgwickAHRSupdateIMU(gx, gy, gz, ax, ay, az);
        return mp_const_none;
    }

    // Rate of change of quaternion from gyroscope
    qDot1 = 0.5f * (-q1 * gx - q2 * gy - q3 * gz);
    qDot2 = 0.5f * (q0 * gx + q2 * gz - q3 * gy);
    qDot3 = 0.5f * (q0 * gy - q1 * gz + q3 * gx);
    qDot4 = 0.5f * (q0 * gz + q1 * gy - q2 * gx);

    // Compute feedback only if accelerometer measurement valid (avoids NaN in accelerometer normalisation)
    if(!((ax == 0.0f) && (ay == 0.0f) && (az == 0.0f))) {

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
        _2q0mx = 2.0f * q0 * mx;
        _2q0my = 2.0f * q0 * my;
        _2q0mz = 2.0f * q0 * mz;
        _2q1mx = 2.0f * q1 * mx;
        _2q0 = 2.0f * q0;
        _2q1 = 2.0f * q1;
        _2q2 = 2.0f * q2;
        _2q3 = 2.0f * q3;
        _2q0q2 = 2.0f * q0 * q2;
        _2q2q3 = 2.0f * q2 * q3;
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
        hx = mx * q0q0 - _2q0my * q3 + _2q0mz * q2 + mx * q1q1 + _2q1 * my * q2 + _2q1 * mz * q3 - mx * q2q2 - mx * q3q3;
        hy = _2q0mx * q3 + my * q0q0 - _2q0mz * q1 + _2q1mx * q2 - my * q1q1 + my * q2q2 + _2q2 * mz * q3 - my * q3q3;
        _2bx = sqrt(hx * hx + hy * hy);
        _2bz = -_2q0mx * q2 + _2q0my * q1 + mz * q0q0 + _2q1mx * q3 - mz * q1q1 + _2q2 * my * q3 - mz * q2q2 + mz * q3q3;
        _4bx = 2.0f * _2bx;
        _4bz = 2.0f * _2bz;

        // Gradient decent algorithm corrective step
        s0 = -_2q2 * (2.0f * q1q3 - _2q0q2 - ax) + _2q1 * (2.0f * q0q1 + _2q2q3 - ay) - _2bz * q2 * (_2bx * (0.5f - q2q2 - q3q3) + _2bz * (q1q3 - q0q2) - mx) + (-_2bx * q3 + _2bz * q1) * (_2bx * (q1q2 - q0q3) + _2bz * (q0q1 + q2q3) - my) + _2bx * q2 * (_2bx * (q0q2 + q1q3) + _2bz * (0.5f - q1q1 - q2q2) - mz);
        s1 = _2q3 * (2.0f * q1q3 - _2q0q2 - ax) + _2q0 * (2.0f * q0q1 + _2q2q3 - ay) - 4.0f * q1 * (1 - 2.0f * q1q1 - 2.0f * q2q2 - az) + _2bz * q3 * (_2bx * (0.5f - q2q2 - q3q3) + _2bz * (q1q3 - q0q2) - mx) + (_2bx * q2 + _2bz * q0) * (_2bx * (q1q2 - q0q3) + _2bz * (q0q1 + q2q3) - my) + (_2bx * q3 - _4bz * q1) * (_2bx * (q0q2 + q1q3) + _2bz * (0.5f - q1q1 - q2q2) - mz);
        s2 = -_2q0 * (2.0f * q1q3 - _2q0q2 - ax) + _2q3 * (2.0f * q0q1 + _2q2q3 - ay) - 4.0f * q2 * (1 - 2.0f * q1q1 - 2.0f * q2q2 - az) + (-_4bx * q2 - _2bz * q0) * (_2bx * (0.5f - q2q2 - q3q3) + _2bz * (q1q3 - q0q2) - mx) + (_2bx * q1 + _2bz * q3) * (_2bx * (q1q2 - q0q3) + _2bz * (q0q1 + q2q3) - my) + (_2bx * q0 - _4bz * q2) * (_2bx * (q0q2 + q1q3) + _2bz * (0.5f - q1q1 - q2q2) - mz);
        s3 = _2q1 * (2.0f * q1q3 - _2q0q2 - ax) + _2q2 * (2.0f * q0q1 + _2q2q3 - ay) + (-_4bx * q3 + _2bz * q1) * (_2bx * (0.5f - q2q2 - q3q3) + _2bz * (q1q3 - q0q2) - mx) + (-_2bx * q0 + _2bz * q2) * (_2bx * (q1q2 - q0q3) + _2bz * (q0q1 + q2q3) - my) + _2bx * q1 * (_2bx * (q0q2 + q1q3) + _2bz * (0.5f - q1q1 - q2q2) - mz);
        recipNorm = invSqrt(s0 * s0 + s1 * s1 + s2 * s2 + s3 * s3); // normalise step magnitude
        s0 *= recipNorm;
        s1 *= recipNorm;
        s2 *= recipNorm;
        s3 *= recipNorm;

        // Apply feedback step
        qDot1 -= beta * s0;
        qDot2 -= beta * s1;
        qDot3 -= beta * s2;
        qDot4 -= beta * s3;
    }

    // Integrate rate of change of quaternion to yield quaternion
    q0 += qDot1 * delta_t_s;
    q1 += qDot2 * delta_t_s;
    q2 += qDot3 * delta_t_s;
    q3 += qDot4 * delta_t_s;

    // Normalise quaternion
    recipNorm = invSqrt(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3);
    q0 *= recipNorm;
    q1 *= recipNorm;
    q2 *= recipNorm;
    q3 *= recipNorm;

    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(madgwick_MadgwickAHRSupdate_obj, 10, 10, madgwick_MadgwickAHRSupdate);

//
//def angle_DOF9()
//
STATIC mp_obj_t madgwick_angle_DOF9() {

    float yaw =  atan2(2.0 * (q1 * q2 + q0 * q3), q0 * q0 + q1 * q1 - q2 * q2 - q3 * q3) * 57.295779513f; // degrees
    float pitch = asin(2.0 * (q1 * q3 - q0 * q2)) * 57.295779513f; // degrees
    float roll = atan2(2.0 * (q0 * q1 + q2 * q3), q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3) * 57.295779513f; // degrees

    // signature: mp_obj_t mp_obj_new_tuple(size_t n, const mp_obj_t *items);
    mp_obj_t ret_val[] = {
        mp_obj_new_float(yaw),
        mp_obj_new_float(pitch),
        mp_obj_new_float(roll),
    };
    return mp_obj_new_tuple(3, ret_val);
}
MP_DEFINE_CONST_FUN_OBJ_0(madgwick_angle_DOF9_obj, madgwick_angle_DOF9);

//---------------------------------------------------------------------------------------------------
// IMU algorithm update

//
//def MadgwickAHRSupdateIMU(gx : float, gy : float, gz : float, ax : float, ay : float, az : float, delta_t_us:int) -> None:
//
STATIC mp_obj_t madgwick_MadgwickAHRSupdateIMU(size_t n_args, const mp_obj_t *args) {
    mp_float_t gx = mp_obj_get_float(args[0]);
    mp_float_t gy = mp_obj_get_float(args[1]);
    mp_float_t gz = mp_obj_get_float(args[2]);
    mp_float_t ax = mp_obj_get_float(args[3]);
    mp_float_t ay = mp_obj_get_float(args[4]);
    mp_float_t az = mp_obj_get_float(args[5]);
    mp_int_t delta_t_us = mp_obj_get_int(args[6]);

    float delta_t_s = 0.000001f * delta_t_us;

    float recipNorm;
    float s0, s1, s2, s3;
    float qDot1, qDot2, qDot3, qDot4;
    float _2q0, _2q1, _2q2, _2q3, _4q0, _4q1, _4q2 ,_8q1, _8q2, q0q0, q1q1, q2q2, q3q3;

    // Rate of change of quaternion from gyroscope
    qDot1 = 0.5f * (-q1 * gx - q2 * gy - q3 * gz);
    qDot2 = 0.5f * (q0 * gx + q2 * gz - q3 * gy);
    qDot3 = 0.5f * (q0 * gy - q1 * gz + q3 * gx);
    qDot4 = 0.5f * (q0 * gz + q1 * gy - q2 * gx);

    // Compute feedback only if accelerometer measurement valid (avoids NaN in accelerometer normalisation)
    if(!((ax == 0.0f) && (ay == 0.0f) && (az == 0.0f))) {

        // Normalise accelerometer measurement
        recipNorm = invSqrt(ax * ax + ay * ay + az * az);
        ax *= recipNorm;
        ay *= recipNorm;
        az *= recipNorm;

        // Auxiliary variables to avoid repeated arithmetic
        _2q0 = 2.0f * q0;
        _2q1 = 2.0f * q1;
        _2q2 = 2.0f * q2;
        _2q3 = 2.0f * q3;
        _4q0 = 4.0f * q0;
        _4q1 = 4.0f * q1;
        _4q2 = 4.0f * q2;
        _8q1 = 8.0f * q1;
        _8q2 = 8.0f * q2;
        q0q0 = q0 * q0;
        q1q1 = q1 * q1;
        q2q2 = q2 * q2;
        q3q3 = q3 * q3;

        // Gradient decent algorithm corrective step
        s0 = _4q0 * q2q2 + _2q2 * ax + _4q0 * q1q1 - _2q1 * ay;
        s1 = _4q1 * q3q3 - _2q3 * ax + 4.0f * q0q0 * q1 - _2q0 * ay - _4q1 + _8q1 * q1q1 + _8q1 * q2q2 + _4q1 * az;
        s2 = 4.0f * q0q0 * q2 + _2q0 * ax + _4q2 * q3q3 - _2q3 * ay - _4q2 + _8q2 * q1q1 + _8q2 * q2q2 + _4q2 * az;
        s3 = 4.0f * q1q1 * q3 - _2q1 * ax + 4.0f * q2q2 * q3 - _2q2 * ay;
        recipNorm = invSqrt(s0 * s0 + s1 * s1 + s2 * s2 + s3 * s3); // normalise step magnitude
        s0 *= recipNorm;
        s1 *= recipNorm;
        s2 *= recipNorm;
        s3 *= recipNorm;

        // Apply feedback step
        qDot1 -= beta * s0;
        qDot2 -= beta * s1;
        qDot3 -= beta * s2;
        qDot4 -= beta * s3;
    }

    // Integrate rate of change of quaternion to yield quaternion
    q0 += qDot1 * delta_t_s;
    q1 += qDot2 * delta_t_s;
    q2 += qDot3 * delta_t_s;
    q3 += qDot4 * delta_t_s;

    // Normalise quaternion
    recipNorm = invSqrt(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3);
    q0 *= recipNorm;
    q1 *= recipNorm;
    q2 *= recipNorm;
    q3 *= recipNorm;

    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(madgwick_MadgwickAHRSupdateIMU_obj, 7, 7, madgwick_MadgwickAHRSupdateIMU);

//
//def angle_DOF6()
//
STATIC mp_obj_t madgwick_angle_DOF6() {

    float pitch = asin(2.0 * (q1 * q3 - q0 * q2)) * 57.295779513f; // degrees
    float roll = atan2(2.0 * (q0 * q1 + q2 * q3), q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3) * 57.295779513f; // degrees

    // signature: mp_obj_t mp_obj_new_tuple(size_t n, const mp_obj_t *items);
    mp_obj_t ret_val[] = {
        mp_obj_new_float(pitch),
        mp_obj_new_float(roll),
    };
    return mp_obj_new_tuple(2, ret_val);
}
MP_DEFINE_CONST_FUN_OBJ_0(madgwick_angle_DOF6_obj, madgwick_angle_DOF6);

//---------------------------------------------------------------------------------------------------

//def get_beta() -> float:
//
STATIC mp_obj_t madgwick_get_beta() {
    mp_float_t ret_val;

    ret_val = beta;

    return mp_obj_new_float(ret_val);
}
MP_DEFINE_CONST_FUN_OBJ_0(madgwick_get_beta_obj, madgwick_get_beta);

//
//def set_beta(beta : float) -> None:
//
STATIC mp_obj_t madgwick_set_beta(mp_obj_t beta_obj) {
    mp_float_t _beta = mp_obj_get_float(beta_obj);

    beta = _beta;

    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_1(madgwick_set_beta_obj, madgwick_set_beta);

STATIC const mp_rom_map_elem_t madgwick_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_madgwick) },
    { MP_ROM_QSTR(MP_QSTR_MadgwickAHRSupdate), MP_ROM_PTR(&madgwick_MadgwickAHRSupdate_obj) },
    { MP_ROM_QSTR(MP_QSTR_MadgwickAHRSupdateIMU), MP_ROM_PTR(&madgwick_MadgwickAHRSupdateIMU_obj) },
	{ MP_ROM_QSTR(MP_QSTR_angle_DOF6), MP_ROM_PTR(&madgwick_angle_DOF6_obj) },
	{ MP_ROM_QSTR(MP_QSTR_angle_DOF9), MP_ROM_PTR(&madgwick_angle_DOF9_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_beta), MP_ROM_PTR(&madgwick_get_beta_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_beta), MP_ROM_PTR(&madgwick_set_beta_obj) },
};

STATIC MP_DEFINE_CONST_DICT(madgwick_module_globals, madgwick_module_globals_table);
const mp_obj_module_t madgwick_user_cmodule = {
    .base = {&mp_type_module},
    .globals = (mp_obj_dict_t*)&madgwick_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_madgwick, madgwick_user_cmodule, MODULE_MADGWICK_ENABLED);
