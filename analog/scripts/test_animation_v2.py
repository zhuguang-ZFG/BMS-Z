"""V2 时间轴与静帧的一致性；不把画面内容重复抄进测试。"""
import json
import importlib
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.visuals.timeline import Beat, Timeline
from scripts.visuals.render import Layer, scene_svg, static_svg, storyboard_svg
from scripts.visuals.primitives import current_flow, reveal_path, parameter_sweep, camera, combine

NS = {"s": "http://www.w3.org/2000/svg"}


def fixture():
    beats = tuple(Beat(f"拍{i}", i, i + 1, f"第{i}拍的说明 & <变化>", hold=i == 5)
                  for i in range(6))
    tl = Timeline(960, 620, 6, beats, "标题 & <参数>")
    layers = [Layer(None, '<text x="10" y="20">常驻</text>')]
    layers += [Layer(b.name, f'<circle data-sample="{i}" cx="{100 + i}" cy="100" r="10"/>', (3, 4))
               for i, b in enumerate(beats)]
    return tl, layers


class AnimationV2Tests(unittest.TestCase):
    def test_final_caption_waits_for_its_beat(self):
        tl, layers = fixture()
        tree = ET.fromstring(scene_svg(tl, layers))
        final = next(n for n in tree.iter() if n.get("data-caption") == "拍5")
        self.assertEqual("0", final.get("opacity"))
        self.assertEqual("5s", final.find("s:animate", NS).get("begin"))

    def test_storyboard_never_contains_next_beats_geometry(self):
        tl, layers = fixture()
        tree = ET.fromstring(storyboard_svg(tl, layers))
        frames = [n for n in tree.iter() if n.get("data-storyboard-beat")]
        self.assertEqual(5, len(frames))
        for frame in frames:
            index = frame.get("data-storyboard-beat")[1:]
            self.assertEqual([index], [n.get("data-sample") for n in frame.iter() if n.get("data-sample")])

    def test_unselected_storyboard_beat_still_keeps_its_caption(self):
        tl, layers = fixture()
        text = "".join(ET.fromstring(storyboard_svg(tl, layers)).itertext())
        for beat in tl.beats:
            self.assertIn(beat.caption, text)

    def test_static_keeps_only_final_and_persistent_layers_with_final_transform(self):
        tl, layers = fixture()
        tree = ET.fromstring(static_svg(tl, layers))
        self.assertEqual(["5"], [n.get("data-sample") for n in tree.iter() if n.get("data-sample")])
        self.assertTrue(any(n.get("transform") == "translate(3 4)" for n in tree.iter()))
        self.assertFalse(any(n.tag.rsplit("}", 1)[-1].startswith("animate") for n in tree.iter()))

    def test_timeline_metadata_is_parseable_and_complete(self):
        tl, layers = fixture()
        tree = ET.fromstring(scene_svg(tl, layers))
        data = json.loads(tree.find("s:metadata", NS).text)
        self.assertEqual(6, data["duration"])
        self.assertEqual([b.name for b in tl.beats], [b["name"] for b in data["beats"]])

    def test_invalid_timeline_rejected(self):
        tl, _ = fixture()
        with self.assertRaises(ValueError):
            Timeline(960, 620, 99, tl.beats, "broken")
        with self.assertRaises(ValueError):
            Timeline(960, 620, 6, tl.beats[:-1], "broken")

    def test_symptom_record_survives_final_and_print_frames(self):
        from scripts.visuals.scenes.ch17_symptom_four_fields import FIELDS, scene

        tl, layers = scene()
        values = [field[1] for field in FIELDS]
        final = ET.fromstring(static_svg(tl, layers))
        final_text = {node.text for node in final.findall('.//s:text', NS)}
        self.assertEqual(set(values), set(values) & final_text,
                         '结论静帧必须保留四项已填写记录')

        completed = {tl.beats[0].name: 0, tl.beats[-1].name: len(values)}
        completed.update((beat.name, index)
                         for index, beat in enumerate(tl.beats[1:-1], 1))
        storyboard = ET.fromstring(storyboard_svg(tl, layers))
        for frame in storyboard.iter():
            beat = frame.get('data-storyboard-beat')
            if beat is None:
                continue
            with self.subTest(beat=beat):
                frame_text = {node.text for node in frame.findall('.//s:text', NS)}
                self.assertEqual(set(values[:completed[beat]]), set(values) & frame_text,
                                 '分镜须保留已填记录，且不能提前显示后续记录')

    def test_sample_hold_final_frame_keeps_full_trace(self):
        from scripts.visuals.scenes.ch08_sample_hold_v2 import scene

        tl, layers = scene()
        static = static_svg(tl, layers)
        for segment in ('M110,400', '520,180', 'L700,180', '864,220'):
            with self.subTest(segment=segment):
                self.assertIn(segment, static, '结论帧必须保留完整采样周期波形')

    def test_transfer_gate_markers_share_the_voltage_axis(self):
        from scripts.visuals.scenes.ch08_transfer_gate_v2 import scene

        tl, layers = scene()
        animated = ET.fromstring(scene_svg(tl, layers))
        static = ET.fromstring(static_svg(tl, layers))
        storyboard = ET.fromstring(storyboard_svg(tl, layers))
        views = [animated, static]
        views.extend(node for node in storyboard.iter()
                     if node.get('data-storyboard-beat') is not None)
        for index, view in enumerate(views):
            with self.subTest(view=index):
                texts = view.findall('.//s:text', NS)
                zero = next(node for node in texts if node.text in ('0V', 'VIN 0V'))
                full = next(node for node in texts if node.text == '5V')
                x0, x5 = float(zero.get('x')), float(full.get('x'))
                for label, voltage in (('2.5V 门限', 2.5), ('4V', 4)):
                    marker = next(node for node in texts if node.text == label)
                    fraction = (float(marker.get('x')) - x0) / (x5 - x0)
                    self.assertAlmostEqual(voltage / 5, fraction, places=5,
                                           msg='数值标记必须按同一横轴比例放置')


    def test_transfer_gate_envelope_matches_the_stated_resistance_model(self):
        from scripts.visuals.scenes.ch08_transfer_gate_v2 import AMBER, BLUE, GREEN, RULE, scene

        tl, layers = scene()
        root = ET.fromstring(static_svg(tl, layers))
        texts = root.findall('.//s:text', NS)
        self.assertIn('20Ω', [node.text for node in texts],
                      '定量电阻曲线必须显示可用来读数的电阻刻度')
        x0 = float(next(node for node in texts if node.text == '0V').get('x'))
        x5 = float(next(node for node in texts if node.text == '5V').get('x'))
        axes = root.findall('.//s:line', NS)
        y_zero = float(next(line for line in axes
                            if line.get('stroke') == RULE
                            and float(line.get('x1')) == x0
                            and float(line.get('x2')) == x5
                            and line.get('y1') == line.get('y2')).get('y1'))
        tick = float(next(node for node in texts if node.text == '20Ω').get('y'))
        grid = [float(line.get('y1')) for line in axes
                if line.get('stroke') == RULE and line.get('stroke-dasharray')
                and line.get('y1') == line.get('y2')]
        y_twenty = min(grid, key=lambda y: abs(y - tick))
        def read_curve(colour):
            curve = next(node for node in root.findall('.//s:polyline', NS)
                         if node.get('stroke') == colour)
            points = []
            for pair in curve.get('points').split():
                x, y = map(float, pair.split(','))
                voltage = 5 * (x - x0) / (x5 - x0)
                resistance = 20 * (y_zero - y) / (y_zero - y_twenty)
                points.append((voltage, resistance))
            return points

        samples = read_curve(GREEN)
        for voltage, expected in ((0, 20), (1, 80 / 3), (2.5, 80 / 3),
                                  (4, 80 / 3), (5, 20)):
            with self.subTest(voltage=voltage):
                measured_voltage, measured_resistance = min(
                    samples, key=lambda point: abs(point[0] - voltage))
                self.assertAlmostEqual(voltage, measured_voltage, places=4)
                self.assertAlmostEqual(expected, measured_resistance, delta=0.02)
        plateau = [resistance for voltage, resistance in samples if 1 <= voltage <= 4]
        self.assertLess(max(plateau) - min(plateau), 0.02,
                        '同一教学模型的两管电导和恒定，平台不能画成任意鼓包')
        for colour, channel in ((BLUE, 'N'), (AMBER, 'P')):
            for voltage, resistance in read_curve(colour):
                with self.subTest(channel=channel, voltage=voltage):
                    overdrive = 4 - voltage if channel == 'N' else voltage - 1
                    self.assertGreater(overdrive, 0,
                                       '截止区不能画成有限导通电阻')
                    self.assertAlmostEqual(80 / overdrive, resistance, delta=0.02)

    def test_mux_protected_frames_block_transients_before_sampling(self):
        import re
        from scripts.visuals.scenes import ch08_mux_address_glitch_v2 as mux

        tl, layers = mux.scene()
        animated = ET.fromstring(scene_svg(tl, layers))
        storyboard = ET.fromstring(storyboard_svg(tl, layers))
        views = [ET.fromstring(static_svg(tl, layers))]
        for name in ('先拉INH', '等够再采'):
            views.append(next(node for node in animated.iter()
                              if node.get('data-beat') == name))
            views.append(next(node for node in storyboard.iter()
                              if node.get('data-storyboard-beat') == name))
        for index, view in enumerate(views):
            with self.subTest(view=index):
                texts = view.findall('.//s:text', NS)
                visible = ' '.join(node.text or '' for node in texts)
                self.assertNotIn('先导通', visible,
                                 'INH 高电平期间不能同时声称错误通道导通')
                self.assertIn('全断', visible)
                addresses = [node for node in texts if node.text in ('111', '100')]
                self.assertEqual({'111', '100'}, {node.text for node in addresses})
                pulse = next(path for path in view.findall('.//s:path', NS)
                             if path.get('stroke') == mux.GREEN)
                coordinates = [float(value) for value in re.findall(
                    r'-?\d+(?:\.\d+)?', pulse.get('d'))]
                points = list(zip(coordinates[::2], coordinates[1::2]))
                high_y = min(y for _, y in points)
                high_x = [x for x, y in points if y == high_y]
                self.assertGreater(points[0][1], high_y)
                self.assertGreater(points[-1][1], high_y)
                self.assertLess(min(high_x), min(float(node.get('x')) for node in addresses),
                                '先禁止，再改变地址')
                self.assertGreater(max(high_x), max(float(node.get('x')) for node in addresses),
                                   '地址稳定后才能解除禁止')
                sample = next(line for line in view.findall('.//s:line', NS)
                              if line.get('stroke') == mux.PURPLE)
                self.assertGreater(float(sample.get('x1')), max(high_x),
                                   '解除 INH 后仍需等待，再开启采样窗')


    def test_virtual_short_feedback_connects_output_to_inverting_input(self):
        from scripts.visuals.scenes import ch17_virtual_short_probe as source

        tl, layers = source.scene()
        storyboard = ET.fromstring(storyboard_svg(tl, layers))
        views = [ET.fromstring(scene_svg(tl, layers)),
                 ET.fromstring(static_svg(tl, layers))]
        views.extend(node for node in storyboard.iter()
                     if node.get('data-storyboard-beat') is not None)
        for index, view in enumerate(views):
            with self.subTest(view=index):
                resistors = [node for node in view.findall('.//s:rect', NS)
                             if node.get('data-component') == 'Rf']
                self.assertEqual(1, len(resistors), '量虚短前须画清实际要核对的反馈路径')
                resistor = resistors[0]
                triangle = next(node for node in view.findall('.//s:polygon', NS)
                                if len(node.get('points').split()) == 3)
                vertices = [tuple(map(float, pair.split(',')))
                            for pair in triangle.get('points').split()]
                side_x = min(x for x, _ in vertices)
                tip_x, tip_y = max(vertices)
                signal_lines = [node for node in view.findall('.//s:line', NS)
                                if node.get('stroke') == source.INK]
                inputs = sorted((float(line.get('y1')), line) for line in signal_lines
                                if float(line.get('x2')) == side_x
                                and line.get('y1') == line.get('y2'))
                self.assertEqual(2, len(inputs))
                output = next(line for line in signal_lines
                              if float(line.get('x1')) == tip_x
                              and float(line.get('y1')) == tip_y)
                graph = {}

                def connect(a, b):
                    graph.setdefault(a, set()).add(b)
                    graph.setdefault(b, set()).add(a)

                for wire in view.findall('.//s:polyline', NS):
                    if wire.get('stroke') != source.GREEN:
                        continue
                    points = [tuple(map(float, pair.split(',')))
                              for pair in wire.get('points').split()]
                    for a, b in zip(points, points[1:]):
                        connect(a, b)
                x, y, w, h = (float(resistor.get(key)) for key in ('x', 'y', 'width', 'height'))
                connect((x, y + h / 2), (x + w, y + h / 2))

                def touches(line):
                    x1, x2, y = (float(line.get(key)) for key in ('x1', 'x2', 'y1'))
                    return [point for point in graph if point[1] == y
                            and min(x1, x2) <= point[0] <= max(x1, x2)]

                minus = touches(inputs[0][1])
                self.assertEqual(1, len(minus), '反馈回到反相端节点')
                self.assertEqual([], touches(inputs[1][1]), '不得误画成同相正反馈')
                contacts = touches(output)
                self.assertEqual(1, len(contacts), '反馈必须取自输出节点')
                reached, pending = set(), contacts[:]
                while pending:
                    point = pending.pop()
                    if point not in reached:
                        reached.add(point)
                        pending.extend(graph[point] - reached)
                self.assertIn(minus[0], reached, '反馈线与电阻不能在图上断开')

    def test_virtual_short_final_frame_keeps_both_readings(self):
        from scripts.visuals.scenes.ch17_virtual_short_probe import scene

        tl, layers = scene()
        static = static_svg(tl, layers)
        for needle in ('2.500V', '2.508V', '8mV'):
            with self.subTest(needle=needle):
                self.assertIn(needle, static, '结论帧必须保留两次读数与压差')
        self.assertNotIn('读数：—', static, '结论帧不得退回占位读数')

    def test_source_curves_keep_voltage_or_current_constant(self):
        from scripts.visuals.scenes import ch00_source_types_v2 as source

        tl, layers = source.scene()
        animated = ET.fromstring(scene_svg(tl, layers))
        static = ET.fromstring(static_svg(tl, layers))
        storyboard = ET.fromstring(storyboard_svg(tl, layers))
        for name, colour, constant_axis in (
                ('恒压', source.BLUE, 'y'), ('恒流', source.GREEN, 'x')):
            views = [
                next(node for node in animated.iter() if node.get('data-beat') == name),
                static,
                next(node for node in storyboard.iter()
                     if node.get('data-storyboard-beat') == name),
                next(node for node in storyboard.iter()
                     if node.get('data-storyboard-beat') == tl.beats[-1].name),
            ]
            for index, view in enumerate(views):
                with self.subTest(source=name, view=index):
                    curves = [line for line in view.findall('.//s:line', NS)
                              if line.get('stroke') == colour]
                    self.assertEqual(1, len(curves), '各视图须保留对应源的曲线')
                    curve = curves[0]
                    self.assertEqual(float(curve.get(constant_axis + '1')),
                                     float(curve.get(constant_axis + '2')),
                                     '横轴 I、纵轴 V：恒压固定纵坐标，恒流固定横坐标')
                    varying_axis = 'x' if constant_axis == 'y' else 'y'
                    self.assertNotEqual(float(curve.get(varying_axis + '1')),
                                        float(curve.get(varying_axis + '2')))

    def test_divider_loading_final_frame_keeps_load_branch(self):
        from scripts.visuals.scenes.ch00_divider_loading_v2 import scene

        tl, layers = scene()
        static = static_svg(tl, layers)
        self.assertIn('RL 10kΩ', static, '结论帧必须保留负载支路')
        self.assertIn('<rect x="624" y="380" width="32" height="46"', static, '负载电阻要画出来')

    def test_all_real_scenes_reproduce_checked_in_triplets(self):
        root = Path(__file__).resolve().parents[1]
        for source in sorted((root / 'scripts/visuals/scenes').glob('ch*.py')):
            module = importlib.import_module('scripts.visuals.scenes.' + source.stem)
            if not hasattr(module, 'scene'):  # 同目录允许静态插图场景。
                continue
            tl, layers = module.scene()
            for suffix, build in [('', scene_svg), ('-static', static_svg), ('-storyboard', storyboard_svg)]:
                output = root / 'assets/svg-v2' / (source.stem.replace('_', '-') + suffix + '.svg')
                expected = module.storyboard() if suffix == '-storyboard' and hasattr(module, 'storyboard') else build(tl, layers)
                self.assertEqual(expected, output.read_text(encoding='utf-8'), str(output))

    def test_moving_primitives_have_static_print_snapshots(self):
        tl, _ = fixture()
        graphic = combine(current_flow('M0 0L10 10', 5, .8),
                          reveal_path('M0 0L10 10', 5, .8),
                          parameter_sweep(20, 10, 30, 5, .8, '末值'),
                          camera('<rect width="10" height="10"/>', 5, .8, dx=5))
        animated = scene_svg(tl, [Layer('拍5', graphic)])
        static = static_svg(tl, [Layer('拍5', graphic)])
        self.assertIn('<animateMotion', animated)
        self.assertNotIn('<animate', static)
        self.assertIn('cx="30"', static)


if __name__ == "__main__":
    unittest.main()
