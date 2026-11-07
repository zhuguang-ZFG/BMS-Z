"""用 python code/course/learn.py init --work my_bms.py 复制为自己的作业。

第 04 课已经写好，从第 05 课开始，每次只完成当前课的函数。
把该函数中的 raise NotImplementedError(...) 换成自己的计算，保存后再检查。
尚未学到的函数可以留着；--through 指定检查到哪一课。
各输入的单位和返回值要求见 docs/course/ 中对应课文。
"""
import binascii  # noqa: F401 - 第 17 课校验字节时使用
import math  # noqa: F401 - 第 06 课检查数值时使用
import struct  # noqa: F401 - 第 16 课解码时使用


def pack_voltage(cells):
    return sum(cells)


def calibrate(raw_v, offset_v):
    raise NotImplementedError("05: 待完成；原始电压减去已确认的偏移，注意正负号")


def sample_ok(cells, sampled_s, now_s, max_age_s):
    raise NotImplementedError("06: 待完成；检查四节电压的数值、范围与样本年龄")


def violations(cells, low_v, high_v):
    raise NotImplementedError("07: 待完成；逐节判断是否越线，等于上下限也算越线")


def trip_at(times, unsafe, delay_s):
    raise NotImplementedError("08: 待完成；按连续越线的秒数找首次动作时刻")


def can_reset(manual, safe, feedback_open):
    raise NotImplementedError("09: 待完成；人工请求、当前安全、反馈已断开三项都要满足")


def soc_step(soc, current_a, dt_s, capacity_ah):
    raise NotImplementedError("10: 待完成；放电电流为正，时间输入为秒")


def drift(offset_a, hours, capacity_ah):
    raise NotImplementedError("11: 待完成；返回比例，例如5个百分点写成0.05")


def ocv_soc(voltage, low_v, high_v):
    raise NotImplementedError("12: 待完成；按教学直线换算，结果限制在0到1")


def charge_allowed(temp_c, sample_valid, requested):
    raise NotImplementedError("13: 待完成；温度0到45摄氏度含端点，另检查有效与请求")


def balance_hours(delta_ah, current_a):
    raise NotImplementedError("14: 待完成；电量除以泄放电流，检查输入是否有效")


def remaining_ah(capacities, socs):
    raise NotImplementedError("15: 待完成；找出可用电量最少的那节")


def decode(frame):
    raise NotImplementedError("16/17: 先解码；第17课补长度、CRC、范围和质量检查")


def sequence_ok(previous, current):
    raise NotImplementedError("17: 待完成；检查下一序号，255之后回到0")


def remote_enable(local_safe, fresh, requested):
    raise NotImplementedError("18: 待完成；本地允许、消息新鲜、远程请求三项都要满足")
