/* No autoplay: the reader controls the only changing part of the notebook. */
const current = document.getElementById('current');
if (current) {
  const render = () => {
    const amps = Number(current.value);
    const drop = amps * 0.020;
    const voltage = (3.70 - drop).toFixed(2);
    document.getElementById('current-value').textContent = `${amps} A`;
    document.getElementById('meter-voltage').textContent = `${voltage} V`;
    document.getElementById('drop').textContent = drop.toFixed(2);
    const equation = document.getElementById('equation');
    equation.replaceChildren(document.createTextNode(`3.70 − ${amps} × 0.020 = `));
    const result = document.createElement('strong');
    result.textContent = `${voltage} V`;
    equation.append(result);
    current.setAttribute('aria-valuetext', `${amps} 安，端电压 ${voltage} 伏，欧姆压降 ${drop.toFixed(2)} 伏`);
    document.getElementById('meter-desc').textContent = `教学模型：开路电压 3.70 伏，内阻 20 毫欧；${amps} 安放电时端电压 ${voltage} 伏。`;
  };
  document.querySelector('.experiment').hidden = false;
  current.addEventListener('input', render);
  render();
}
