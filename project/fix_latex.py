"""
Script to scan and fix all raw LaTeX mathematical syntax across the generator scripts,
replacing them with clean HTML/Unicode typography for ReportLab.
"""
import os
import re

def clean_file(filepath):
    if not os.path.exists(filepath):
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # Replacements dictionary
    reps = [
        (r'(\$t_1 \\le t_2 \\le \\dots\$)', '(t<sub>1</sub> ≤ t<sub>2</sub> ≤ ... ≤ t<sub>n</sub>)'),
        (r'(\$t_1 \\le t_2 \\le \\dots \\le t_n\$)', '(t<sub>1</sub> ≤ t<sub>2</sub> ≤ ... ≤ t<sub>n</sub>)'),
        (r'\$p_i \\in \[1, 5\]\$', 'p<sub>i</sub> ∈ [1, 5]'),
        (r'\$p_i \\in \\\{1, 2, 3, 4, 5\\\}\$', 'p<sub>i</sub> ∈ {1, 2, 3, 4, 5}'),
        (r'\(Station \$1 \\rightarrow 2 \\rightarrow 3 \\rightarrow 1\$\)', '(Station 1 → Station 2 → Station 3 → Station 1)'),
        (r'Station \$1 \\rightarrow 2 \\rightarrow 3 \\rightarrow 1\$', 'Station 1 → Station 2 → Station 3 → Station 1'),
        (r'\$\(x_0, y_0, z_0\)\$', '(x<sub>0</sub>, y<sub>0</sub>, z<sub>0</sub>)'),
        (r'\(\$C_\{max\}\$\)', '(C<sub>max</sub>)'),
        (r'\(\$W_\{avg\}\$\)', '(W<sub>avg</sub>)'),
        (r'\(\$U_R\$\)', '(U<sub>R</sub>)'),
        (r'\(\$TH\$\)', '(TH)'),
        (r'\(\$U_\{TB3\}\$\)', '(U<sub>TB3</sub>)'),
        (r'\(\$U_\{UR5\}\$\)', '(U<sub>UR5</sub>)'),
        (r'\(\$U_\{UR\}\$\)', '(U<sub>UR</sub>)'),
        (r'\$\\rightarrow\$', '→'),
        (r'\\rightarrow', '→'),
        (r'\$R \\in \\\{\\text\{UR5\}, \\text\{TB3\}\\\}\$', 'R ∈ {UR5, TB3}'),
        (r'\$R \\in \\\{\\text\{UR5/UR16e\}, \\text\{TB3\}\\\}\$', 'R ∈ {UR5/UR16e, TB3}'),
        (r'\$T_\{total\}\$', 'T<sub>total</sub>'),
        (r'\$p_i = 1\$', 'p<sub>i</sub> = 1'),
        (r'\$p_i = 5\$', 'p<sub>i</sub> = 5'),
        (r'\$T_i\$', 'T<sub>i</sub>'),
        (r'\$M\$', 'M'),
        (r'\$O\(1\)\$', 'O(1)'),
        (r'\$O\(\\log n\)\$', 'O(log N)'),
        (r'\$O\(\\log N\)\$', 'O(log N)'),
        (r'\$\$W_\{avg\} = \\\\frac\{1\}\{N\} \\\\sum_\{i=1\}\^N \(t_\{start, i\} - t_\{arrival, i\}\)\$\$', '<b>W<sub>avg</sub> = (1 / N) · ∑<sub>i=1..N</sub> (t<sub>start, i</sub> − t<sub>arrival, i</sub>)</b>'),
        (r'\$\$W_\{avg\} = \\frac\{1\}\{N\} \\sum_\{i=1\}\^N \(t_\{start, i\} - t_\{arrival, i\}\)\$\$', '<b>W<sub>avg</sub> = (1 / N) · ∑<sub>i=1..N</sub> (t<sub>start, i</sub> − t<sub>arrival, i</sub>)</b>'),
        (r'\$\$U_R = \\\\left\( \\\\frac\{\\\\sum_\{i=1\}\^N \\\\tau_\{busy, R, i\}\}\{T_\{total\}\} \\\\right\) \\\\times 100\\\\%\$\$', '<b>U<sub>R</sub> = [ ( ∑ τ<sub>busy, R, i</sub> ) / T<sub>total</sub> ] × 100%</b>'),
        (r'\$\$U_R = \\left\( \\frac\{\\sum_\{i=1\}\^N \\tau_\{busy, R, i\}\}\{T_\{total\}\} \\right\) \\times 100\\%\$\$', '<b>U<sub>R</sub> = [ ( ∑ τ<sub>busy, R, i</sub> ) / T<sub>total</sub> ] × 100%</b>'),
        (r'\$\$TH = \\\\left\( \\\\frac\{N_\{completed\}\}\{T_\{total\}\} \\\\right\) \\\\times 3600\$\$', '<b>TH = ( N<sub>completed</sub> / T<sub>total</sub> ) × 3600 &nbsp; (Tasks / Hour)</b>'),
        (r'\$\$TH = \\left\( \\frac\{N_\{completed\}\}\{T_\{total\}\} \\right\) \\times 3600\$\$', '<b>TH = ( N<sub>completed</sub> / T<sub>total</sub> ) × 3600 &nbsp; (Tasks / Hour)</b>'),
        (r'\$\^\{map\}\\\\mathbf\{T\}_\{ee\} = \^\{map\}\\\\mathbf\{T\}_\{odom\} \\\\cdot \^\{odom\}\\\\mathbf\{T\}_\{base\} \\\\cdot \^\{base\}\\\\mathbf\{T\}_\{arm\\\\_base\} \\\\cdot \^\{arm\\\\_base\}\\\\mathbf\{T\}_\{ee\}\(\\\\theta_1, \\\\theta_2, \\\\theta_3, \\\\theta_4\)\$', '<sup>map</sup><b>T</b><sub>ee</sub> = <sup>map</sup><b>T</b><sub>odom</sub> · <sup>odom</sup><b>T</b><sub>base</sub> · <sup>base</sup><b>T</b><sub>arm_base</sub> · <sup>arm_base</sup><b>T</b><sub>ee</sub>(θ<sub>1</sub>, θ<sub>2</sub>, θ<sub>3</sub>, θ<sub>4</sub>)'),
        (r'\$\$P_i\(t\) = \\\\alpha \\\\cdot u_i \+ \\\\beta \\\\cdot \(t - t_\{arrival, i\}\) \+ \\\\gamma \\\\cdot \\\\frac\{1\}\{B_\{robot\}\(t\)\}\$\$', '<b>P<sub>i</sub>(t) = α · u<sub>i</sub> + β · (t − t<sub>arrival, i</sub>) + γ · [1 / B<sub>robot</sub>(t)]</b>'),
        (r'\$\$D_i = \\\\tau_\{nav\}\(\\\\mathbf\{x\}_\{start\}, \\\\mathbf\{x\}_\{target\}\) \+ \\\\tau_\{manip\}\(\\\\theta_\{initial\}, \\\\theta_\{final\}\) \+ \\\\delta_\{comm\}\$\$', '<b>D<sub>i</sub> = τ<sub>nav</sub>(x<sub>start</sub>, x<sub>target</sub>) + τ<sub>manip</sub>(θ<sub>initial</sub>, θ<sub>final</sub>) + δ<sub>comm</sub></b>'),
    ]

    for pat, rep in reps:
        text = re.sub(pat, rep, text)

    # General cleanup of any lingering math delimiters
    text = text.replace(r'\\Delta t_{fb}', 'Δt<sub>fb</sub>')
    text = text.replace(r'\\mathcal{C}_{preempt}', 'C<sub>preempt</sub>')
    text = text.replace(r'\\mathcal{S}', 'S')
    text = text.replace(r'\\{', '{').replace(r'\\}', '}')
    text = text.replace(r'\\text{', '').replace(r'}', '') # cleans any raw \text tags

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Cleaned LaTeX in {filepath}")

for fp in [
    'generate_massive_report.py',
    'generate_master_report.py',
    'generate_pdf_report.py',
    'generate_individual_papers.py'
]:
    clean_file(fp)
