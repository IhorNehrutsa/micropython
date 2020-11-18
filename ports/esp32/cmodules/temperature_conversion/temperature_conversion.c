// Include required definitions first.
#include "py/obj.h"
#include "py/runtime.h"
#include "py/builtin.h"

//
//def Celsius_from_Fahrenheit(Fahrenheit : float) -> float:
//
STATIC mp_obj_t temperature_conversion_Celsius_from_Fahrenheit(mp_obj_t Fahrenheit_obj) {
    mp_float_t Fahrenheit = mp_obj_get_float(Fahrenheit_obj);

    return mp_obj_new_float((Fahrenheit - 32.0f) * 5.0f / 9.0f);
}
MP_DEFINE_CONST_FUN_OBJ_1(temperature_conversion_Celsius_from_Fahrenheit_obj, temperature_conversion_Celsius_from_Fahrenheit);

//
//def Fahrenheit_from_Celsius(Celsius : float) -> float:
//
STATIC mp_obj_t temperature_conversion_Fahrenheit_from_Celsius(mp_obj_t Celsius_obj) {
    mp_float_t Celsius = mp_obj_get_float(Celsius_obj);

    return mp_obj_new_float(Celsius * 1.8f + 32.0f);
}
MP_DEFINE_CONST_FUN_OBJ_1(temperature_conversion_Fahrenheit_from_Celsius_obj, temperature_conversion_Fahrenheit_from_Celsius);

STATIC const mp_rom_map_elem_t temperature_conversion_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_temperature_conversion) },
    { MP_ROM_QSTR(MP_QSTR_Celsius_from_Fahrenheit), MP_ROM_PTR(&temperature_conversion_Celsius_from_Fahrenheit_obj) },
    { MP_ROM_QSTR(MP_QSTR_Fahrenheit_from_Celsius), MP_ROM_PTR(&temperature_conversion_Fahrenheit_from_Celsius_obj) },
};

STATIC MP_DEFINE_CONST_DICT(temperature_conversion_module_globals, temperature_conversion_module_globals_table);
const mp_obj_module_t temperature_conversion_user_cmodule = {
    .base = {&mp_type_module},
    .globals = (mp_obj_dict_t*)&temperature_conversion_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_temperature_conversion, temperature_conversion_user_cmodule, MODULE_TEMPERATURE_CONVERSION_ENABLED);
