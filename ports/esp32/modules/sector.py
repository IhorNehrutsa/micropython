# sector.py
from utime import time

from Owl_API import value_cmp, handle_ros_command, print_motor

import config_version


rpm_high_save = 0
rpm_low_save = 0

motor_state = -1

def handle_sector(owl, motor, ros_params):
    global rpm_high_save, rpm_low_save

#     global motor_state
#     if motor_state != motor.state:
#         print('motor_state <- motor.state', motor_state, motor.state)
#         motor_state = motor.state

    # Поиск глобального максимального уровня в секторе.
    handle_ros_command(owl)
    if owl.value_now is None:
        return
    v = owl.value_now
    if owl.mode == owl.MD_SECTOR_A:
        a = owl.azim_angle_now
    else:
        a = owl.elev_angle_now
    a = round(a, 1)

    if len(v) > 0:
        if len(motor.value_start) == 0:
            motor.value_start = v  # обнаружен сигнал
            motor.angle_start = a  # в этой позиции

    if motor.state == 0:  # очищаем исходные
        owl.sector_time = time()
        #owl.ros_command2 = ["/interface/wireless/set", "=.id=wlan1", "=tx-chains=0,1", "=rx-chains=0,1"]
        if len(v):
            owl.ros_command2 = ["/system/script/run", "=.id=communication"]
        else:
            owl.ros_command2 = ["/system/script/run", "=.id=search"]

        owl.sector_counter = 0
        if (a >= motor.max_search):
            motor.search_dir = -1
            owl.sector_counter = 1  # будет полный сектор
        elif (a <= motor.min_search):
            motor.search_dir = 1
            owl.sector_counter = 1  # будет полный сектор
        elif (motor.max_search - a) <= (a - motor.min_search):
            motor.search_dir = 1
        else:
            motor.search_dir = -1

        if len(v):
            owl.ros_best = v
            motor.angle_best = a
            motor.angle_begin = a  # сигнал есть в начале поиска (не будет перезаписан)
        else:
            motor.angle_begin = None  # сигнала нет в начале поиска (не будет перезаписан)
            if owl.mode == owl.MD_SECTOR_A:
                owl.elev.angle_target = 0  # перейти в горизонт

        motor.angle_start = a  # если сигнал отсутствует, то стартовая позиция будет переписана при обнаружении сигнала
        motor.value_start = v

        rpm_high_save = owl.azim.mover.rpm_high
        rpm_low_save = owl.azim.mover.rpm_low

        motor.state = 2

    elif motor.state == 2:
        # даем задание на всю ширину
        if motor.search_dir > 0:
            motor.angle_target = motor.max_search
        else:
            motor.angle_target = motor.min_search

        if owl.mode == owl.MD_SECTOR_A:
            if owl.sector_counter > 4:
                owl.sector_counter = 0
            if owl.sector_counter == 1:
                if owl.elev.angle_best is not None:
                    # сигнал изначально где-то присутствовал, но потерялся
                    owl.elev.angle_target = owl.elev.angle_best  # один проход по лучшему предыдущему углу места
                else:
                    owl.elev.angle_target = 0
            elif owl.sector_counter == 3:
                owl.elev.angle_target = owl.ANTENNA_ANGLE
            elif owl.sector_counter == 4:
                owl.elev.angle_target = - owl.ANTENNA_ANGLE
            else:
                owl.elev.angle_target = 0

            if owl.sector_counter == 2:
                owl.azim.mover.rpm_high = owl.azim.mover.rpm_high / 5
                owl.azim.mover.rpm_low = owl.azim.mover.rpm_low / 5
            else:
                owl.azim.mover.rpm_high = rpm_high_save
                owl.azim.mover.rpm_low = rpm_low_save

#             print('owl.azim.mover.rpm_high, owl.azim.mover.rpm_low', owl.azim.mover.rpm_high, owl.azim.mover.rpm_low, motor.mover.rpm)
#             print('Поиск по азимуту owl.azim.angle_target=', owl.azim.angle_target, ', owl.elev.angle_target=', owl.elev.angle_target, ', owl.sector_counter = ', owl.sector_counter)
#             print()

        owl.sector_counter += 1
        motor.state = 3

    elif motor.state == 3:
        # Проверяем достижение границ сектора
        if motor.mover.is_ready() \
        or (motor.search_dir > 0) and (a >= motor.max_search) \
        or (motor.search_dir < 0) and (a <= motor.min_search):
            motor.mover.stop()
            if (motor.angle_begin is None) and len(v):
                motor.angle_begin = a
                owl.sector_counter = 0  # впервые обнаружен сигнал(возможно корреспондент включился позже, поймали на исходе), нужно пройти полный сектор поиска

            if motor.angle_best is not None:
                motor.angle_target = motor.angle_best  # идем в лучшее

                owl.azim.mover.rpm_high = rpm_high_save
                owl.azim.mover.rpm_low = rpm_low_save

                #print("owl.sector_counter", owl.sector_counter)
                if owl.sector_counter >= 2:
                    motor.state = 5
                else:
                    motor.search_dir = -motor.search_dir
                    motor.state = 2
            else:
                motor.search_dir = -motor.search_dir
                motor.state = 2  # повторный поиска в противоположном направлении, нужно пройти полный сектор поиска

#     elif motor.state == 35:
#         if motor.mover.is_ready():
#             motor.mover.stop()
#             motor.state = 4
#
#     elif motor.state == 4:
#         if owl.state == owl.CM_NO:
#             motor.mover.stop()
#             if len(v):
#                 motor.search_dir = -motor.search_dir
#                 motor.state = 2  # нет сигнала, переискать
#             else:
#                 owl.state = owl.CM_SEE
#                 owl.azim.mover.pid.output_limits = owl.azim_output_limits  # восстановить скорость
#         elif owl.state == owl.CM_SECTOR:
#             motor.state = 2  # увидели корреспондента, переискать

    elif motor.state == 5:
        # ожидание позиционирования
        if motor.angle_best is not None:
            if motor.angle_best != motor.angle_target:
                motor.angle_target = motor.angle_best  # если по пути найдется еще лучше, то выбираем его
        if motor.mover.is_ready():
            motor.mover.stop()
            motor.state = 8

    elif motor.state == 8:
        motor.mover.stop()
        print_motor(owl, motor, a, v)

        if motor.angle_best is None:  # сигнал не обнаружен
            if owl.mode == owl.MD_SECTOR_A:
                # повторить обзор азиимута сместив угол места
                motor.state = 2
            else:  # owl.mode == owl.MD_SECTOR_E:
                if owl.elev.angle_best is not None:
                    owl.elev.angle_target = owl.elev.angle_best
                else:
                    owl.elev.angle_target = 0
                owl.mode = owl.MD_ESCORT_A  # переключение на режим слежения
        else:
            if owl.mode == owl.MD_SECTOR_A:
                owl.mode = owl.MD_SECTOR_E  # переключение на угол места
            elif owl.azim.angle_best is None:
                owl.mode = owl.MD_SECTOR_A
                print('Сигнал впервые обнаружен в секторе угла места. Поиск по азимуту')
            else:
#                 owl.mode = owl.MD_COMMUNICATE
#                 owl.corr.out = "ID\n"
#                 owl.mode = owl.MD_MANUAL
                owl.mode = owl.MD_ESCORT_A  # переключение на режим слежения
    else:
        print('raise')
        raise
