"""
Precise, safe LaTeX replacement script.
Replaces raw LaTeX strings in string literals with clean HTML/Unicode for ReportLab.
"""
import os

files_to_fix = [
    'generate_massive_report.py',
    'generate_master_report.py',
    'generate_pdf_report.py',
    'generate_individual_papers.py'
]

replacements = [
    # Formulas
    (r'$$W_{avg} = \frac{1}{N} \sum_{i=1}^N (t_{start, i} - t_{arrival, i})$$', '<b>W<sub>avg</sub> = (1 / N) · ∑ (t<sub>start, i</sub> − t<sub>arrival, i</sub>)</b>'),
    (r'$$W_{avg} = \\frac{1}{N} \\sum_{i=1}^N (t_{start, i} - t_{arrival, i})$$', '<b>W<sub>avg</sub> = (1 / N) · ∑ (t<sub>start, i</sub> − t<sub>arrival, i</sub>)</b>'),
    (r'$$U_R = \left( \frac{\sum_{i=1}^N \tau_{busy, R, i}}{T_{total}} \right) \times 100\%$$', '<b>U<sub>R</sub> = [ ( ∑ τ<sub>busy, R, i</sub> ) / T<sub>total</sub> ] × 100%</b>'),
    (r'$$U_R = \\left( \\frac{\\sum_{i=1}^N \\tau_{busy, R, i}}{T_{total}} \\right) \\times 100\\%$$', '<b>U<sub>R</sub> = [ ( ∑ τ<sub>busy, R, i</sub> ) / T<sub>total</sub> ] × 100%</b>'),
    (r'$$TH = \left( \frac{N_{completed}}{T_{total}} \right) \times 3600$$', '<b>TH = ( N<sub>completed</sub> / T<sub>total</sub> ) × 3600 &nbsp; (Tasks / Hour)</b>'),
    (r'$$TH = \\left( \\frac{N_{completed}}{T_{total}} \\right) \\times 3600$$', '<b>TH = ( N<sub>completed</sub> / T<sub>total</sub> ) × 3600 &nbsp; (Tasks / Hour)</b>'),
    (r'$$P_i(t) = \alpha \cdot u_i + \beta \cdot (t - t_{arrival, i}) + \gamma \cdot \frac{1}{B_{robot}(t)}$$', '<b>P<sub>i</sub>(t) = α · u<sub>i</sub> + β · (t − t<sub>arrival, i</sub>) + γ · [1 / B<sub>robot</sub>(t)]</b>'),
    (r'$$P_i(t) = \\alpha \\cdot u_i + \\beta \\cdot (t - t_{arrival, i}) + \\gamma \\cdot \\frac{1}{B_{robot}(t)}$$', '<b>P<sub>i</sub>(t) = α · u<sub>i</sub> + β · (t − t<sub>arrival, i</sub>) + γ · [1 / B<sub>robot</sub>(t)]</b>'),
    (r'$$D_i = \tau_{nav}(\mathbf{x}_{start}, \mathbf{x}_{target}) + \tau_{manip}(\theta_{initial}, \theta_{final}) + \delta_{comm}$$', '<b>D<sub>i</sub> = τ<sub>nav</sub>(x<sub>start</sub>, x<sub>target</sub>) + τ<sub>manip</sub>(θ<sub>initial</sub>, θ<sub>final</sub>) + δ<sub>comm</sub></b>'),
    (r'$$D_i = \\tau_{nav}(\\mathbf{x}_{start}, \\mathbf{x}_{target}) + \\tau_{manip}(\\theta_{initial}, \\theta_{final}) + \\delta_{comm}$$', '<b>D<sub>i</sub> = τ<sub>nav</sub>(x<sub>start</sub>, x<sub>target</sub>) + τ<sub>manip</sub>(θ<sub>initial</sub>, θ<sub>final</sub>) + δ<sub>comm</sub></b>'),
    (r'$^{map}\mathbf{T}_{ee} = ^{map}\mathbf{T}_{odom} \cdot ^{odom}\mathbf{T}_{base} \cdot ^{base}\mathbf{T}_{arm\_base} \cdot ^{arm\_base}\mathbf{T}_{ee}(\theta_1, \theta_2, \theta_3, \theta_4)$', '<sup>map</sup><b>T</b><sub>ee</sub> = <sup>map</sup><b>T</b><sub>odom</sub> · <sup>odom</sup><b>T</b><sub>base</sub> · <sup>base</sup><b>T</b><sub>arm_base</sub> · <sup>arm_base</sup><b>T</b><sub>ee</sub>(θ<sub>1</sub>, θ<sub>2</sub>, θ<sub>3</sub>, θ<sub>4</sub>)'),
    (r'$^{map}\\mathbf{T}_{ee} = ^{map}\\mathbf{T}_{odom} \\cdot ^{odom}\\mathbf{T}_{base} \\cdot ^{base}\\mathbf{T}_{arm\\_base} \\cdot ^{arm\\_base}\\mathbf{T}_{ee}(\\theta_1, \\theta_2, \\theta_3, \\theta_4)$', '<sup>map</sup><b>T</b><sub>ee</sub> = <sup>map</sup><b>T</b><sub>odom</sub> · <sup>odom</sup><b>T</b><sub>base</sub> · <sup>base</sup><b>T</b><sub>arm_base</sub> · <sup>arm_base</sup><b>T</b><sub>ee</sub>(θ<sub>1</sub>, θ<sub>2</sub>, θ<sub>3</sub>, θ<sub>4</sub>)'),

    # Inline Symbols
    (r'($t_1 \le t_2 \le \dots$)', '(t<sub>1</sub> ≤ t<sub>2</sub> ≤ ... ≤ t<sub>n</sub>)'),
    (r'($t_1 \\le t_2 \\le \\dots$)', '(t<sub>1</sub> ≤ t<sub>2</sub> ≤ ... ≤ t<sub>n</sub>)'),
    (r'($t_1 \le t_2 \le \dots \le t_n$)', '(t<sub>1</sub> ≤ t<sub>2</sub> ≤ ... ≤ t<sub>n</sub>)'),
    (r'($t_1 \\le t_2 \\le \\dots \\le t_n$)', '(t<sub>1</sub> ≤ t<sub>2</sub> ≤ ... ≤ t<sub>n</sub>)'),
    (r'$p_i \in [1, 5]$', 'p<sub>i</sub> ∈ [1, 5]'),
    (r'$p_i \\in [1, 5]$', 'p<sub>i</sub> ∈ [1, 5]'),
    (r'$p_i \in \{1, 2, 3, 4, 5\}$', 'p<sub>i</sub> ∈ {1, 2, 3, 4, 5}'),
    (r'$p_i \\in \\{1, 2, 3, 4, 5\\}$', 'p<sub>i</sub> ∈ {1, 2, 3, 4, 5}'),
    (r'(Station $1 \rightarrow 2 \rightarrow 3 \rightarrow 1$)', '(Station 1 → Station 2 → Station 3 → Station 1)'),
    (r'(Station $1 \\rightarrow 2 \\rightarrow 3 \\rightarrow 1$)', '(Station 1 → Station 2 → Station 3 → Station 1)'),
    (r'Station $1 \rightarrow 2 \rightarrow 3 \rightarrow 1$', 'Station 1 → Station 2 → Station 3 → Station 1'),
    (r'Station $1 \\rightarrow 2 \\rightarrow 3 \\rightarrow 1$', 'Station 1 → Station 2 → Station 3 → Station 1'),
    (r'$(x_0, y_0, z_0)$', '(x<sub>0</sub>, y<sub>0</sub>, z<sub>0</sub>)'),
    (r'($C_{max}$)', '(C<sub>max</sub>)'),
    (r'($W_{avg}$)', '(W<sub>avg</sub>)'),
    (r'($U_R$)', '(U<sub>R</sub>)'),
    (r'($TH$)', '(TH)'),
    (r'($U_{TB3}$)', '(U<sub>TB3</sub>)'),
    (r'($U_{UR5}$)', '(U<sub>UR5</sub>)'),
    (r'($U_{UR}$)', '(U<sub>UR</sub>)'),
    (r'$\rightarrow$', '→'),
    (r'$\\rightarrow$', '→'),
    (r'$R \in \{\text{UR5}, \text{TB3}\}$', 'R ∈ {UR5, TB3}'),
    (r'$R \\in \\{\\text{UR5}, \\text{TB3}\\}$', 'R ∈ {UR5, TB3}'),
    (r'$R \in \{\text{UR5/UR16e}, \text{TB3}\}$', 'R ∈ {UR5/UR16e, TB3}'),
    (r'$R \\in \\{\\text{UR5/UR16e}, \\text{TB3}\\}$', 'R ∈ {UR5/UR16e, TB3}'),
    (r'$T_{total}$', 'T<sub>total</sub>'),
    (r'$p_i = 1$', 'p<sub>i</sub> = 1'),
    (r'$p_i = 5$', 'p<sub>i</sub> = 5'),
    (r'$T_i$', 'T<sub>i</sub>'),
    (r'$N$', 'N'),
    (r'$M$', 'M'),
    (r'$O(1)$', 'O(1)'),
    (r'$O(\log n)$', 'O(log N)'),
    (r'$O(\log N)$', 'O(log N)'),
    (r'$O(\\log n)$', 'O(log N)'),
    (r'$O(\\log N)$', 'O(log N)'),
    (r'\Delta t_{fb}', 'Δt<sub>fb</sub>'),
    (r'\\Delta t_{fb}', 'Δt<sub>fb</sub>'),
    (r'\mathcal{C}_{preempt}', 'C<sub>preempt</sub>'),
    (r'\\mathcal{C}_{preempt}', 'C<sub>preempt</sub>'),
    (r'\mathcal{S} = \{\text{IDLE}, \text{GOAL\_SENT}, \text{ACCEPTED}, \text{EXECUTING}, \text{PREEMPTED}, \text{SUCCEEDED}, \text{ABORTED}\}', 'S = {IDLE, GOAL_SENT, ACCEPTED, EXECUTING, PREEMPTED, SUCCEEDED, ABORTED}'),
    (r'\\mathcal{S} = \\{\\text{IDLE}, \\text{GOAL\\_SENT}, \\text{ACCEPTED}, \\text{EXECUTING}, \\text{PREEMPTED}, \\text{SUCCEEDED}, \\text{ABORTED}\\}', 'S = {IDLE, GOAL_SENT, ACCEPTED, EXECUTING, PREEMPTED, SUCCEEDED, ABORTED}'),
    (r'\tau_{nav}', 'τ<sub>nav</sub>'),
    (r'\\tau_{nav}', 'τ<sub>nav</sub>'),
    (r'\tau_{manip}', 'τ<sub>manip</sub>'),
    (r'\\tau_{manip}', 'τ<sub>manip</sub>'),
    (r'\delta_{comm}', 'δ<sub>comm</sub>'),
    (r'\\delta_{comm}', 'δ<sub>comm</sub>'),
]

for filename in files_to_fix:
    if not os.path.exists(filename):
        continue
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    orig = content
    for target, replacement in replacements:
        content = content.replace(target, replacement)

    if content != orig:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully cleaned LaTeX in: {filename}")
    else:
        print(f"No changes required in: {filename}")
