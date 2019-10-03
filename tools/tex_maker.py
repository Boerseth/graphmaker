import numpy as np

def decimals_and_power(number):
    log_10_number = np.log(abs(number)) / np.log(10)
    power = str(int(log_10_number // 1))
    decimals = str(10**(log_10_number % 1))
    sign = "" if (np.sign(number) > 0) else "-"
    return decimals, power, sign


def number_to_scientific_latex(number):
    if number == 0:
        return "0"
    decimals, power, sign = decimals_and_power(number)
    ret_string = sign
    ret_string += decimals[:min(6, len(decimals))]
    if power != "0" and power != "1":
        ret_string += " \\cdot 10^{{ {} }}".format(power)
    elif power == 1:
        ret_string += " \\cdot 10"
    return ret_string


    

def latex_simplified_formula(a,b,c,d,n_cols):
    assert len(a) == len(b) and len(a) == len(c) and len(a) == len(d)
    N = len(a)
    begin_align = "\\begin{align*}\n"
    end_align =  "\\end{align*}\n"
    
    ret_string = ""
    ret_string += begin_align
    ret_string += "x(t) &= \\sum\\limits_{{n=1}}^{{ {} }} ".format(N)
    ret_string += "\\Big[a_n \\cos(2n\\pi t) + b_n \\sin(2n\\pi t) \\Big]\\\\ \n"
    ret_string += "y(t) &= \\sum\\limits_{{n=1}}^{{ {} }} ".format(N)
    ret_string += "\\Big[c_n \\cos(2n\\pi t) + d_n \\sin(2n\\pi t) \\Big]\n"
    ret_string += end_align
    ret_string += "\n"

    ret_string += begin_align
    for n in range(N):
        ret_string += '  '
        for letter, coeff in [('a', a[n]), ('b', b[n]), ('c', c[n]), ('d', d[n])]:
            ret_string += "{}_{{ {} }} &= ".format(letter, n+1)
            ret_string += number_to_scientific_latex(coeff)
            if letter != 'd':
                ret_string += ', & '
            else:
                ret_string += ', \\\\ \n' if (n != N-1) else '\n'
    ret_string += end_align
    return ret_string
    

    

def latex_complete_formula(a,b,c,d,n_cols, n_rows):
    N = len(a)
    assert len(b) == N
    assert len(c) == N
    assert len(d) == N
    
    begin_align = "\\begin{align*}\n"
    end_align =  "\\end{align*}\n"
    empty_line = "& \\\\ \n"

    ret_string = begin_align
    ret_string += "  t \\in \\mathbb{R}\n"
    ret_string += end_align
    ret_string += "\n"

    visual_row_count = 3  # Not used for anything yet...

    ret_string += begin_align
    ret_string += "  x(t) &= "
    for n in range(N):
        if (n % n_cols == 0) and (n > 0):
            ret_string += "& "
        if (n > 0) and (a[n] > 0):
            ret_string += "+ "
        # cosine
        ret_string += number_to_scientific_latex(a[n])
        ret_string += " \\cos ( {} \\cdot 2 \\pi t ) ".format(n + 1)

        # sine
        if (b[n] > 0):
            ret_string += "+ "
        ret_string += number_to_scientific_latex(b[n])
        ret_string += " \\sin ( {} \\cdot 2 \\pi t ) ".format(n + 1)
        
        if (n == N-1) or (n % n_cols == n_cols-1):
            ret_string += "\\\\ \n  "
            visual_row_count += 1

    ret_string += empty_line

    ret_string += "y(t) &= "
    for n in range(N):
        if (n % n_cols == 0) and (n > 0):
            ret_string += "& "
        if (n > 0) and (c[n] > 0):
            ret_string += "+ "
        # cosine
        ret_string += number_to_scientific_latex(c[n])
        ret_string += " \\cos ( {} \\cdot 2 \\pi t ) ".format(n + 1)

        # sine
        if (d[n] > 0):
            ret_string += "+ "
        ret_string += number_to_scientific_latex(d[n])
        ret_string += " \\sin ( {} \\cdot 2 \\pi t ) ".format(n + 1)
        
        if (n == N-1):
            ret_string += " \n"
            visual_row_count += 1
        elif (n % n_cols == n_cols-1):
            ret_string += "\\\\ \n  "
            visual_row_count += 1
                
    ret_string += end_align
    return ret_string



"""
BELOW THIS LINE: OLD STUFF
-------------------------------------------------------------------------------
"""


"""
The separator is surprisingly intricate. Here is the justification:

I want there to be a comma and ampersand between each coefficient,
        ... a_n &= 1.23   , &    a_n+1 &= 4.56   , &   ...
                           ^                      ^
But there must not be any `&` after the `last` coefficient of a line.

Also, if the `final` line of coefficients does not fill all collumns,
say for the case of 3 columns and 4 coefficients,
        a_1 &= 1.2  , &  a_2 &= 3.4  , &  a_3 &= 5.6 \\
        a_4 &= 7.8  , &&&& \\
the trailing ampersands must still be included.

Finally, every line must be ended by a newline, _except_ if it is the
final line of the `d`-coefficients.
        d_1 &= 1.2  , &  d_2 &= 3.4  , &  d_3 &= 5.6 \\
        d_4 &= 7.8  , &&&&
        \end{align*}
"""
def separator(n, N, n_cols, letter):
    is_final = (n == N-1)
    is_last = (n % n_cols == n_cols-1)
    is_d = (letter == 'd')

    if is_last:
        if is_final and is_d:
            return " \n"
        else:
            return ",\\\\ \n"
    else:
        if is_final:
            trailing_ampersands = "&"*(2*(n_cols - 1 - (n%n_cols)))
            ret_string = ""
            ret_string += " " if is_d else ", "
            ret_string += trailing_ampersands
            ret_string += " \n" if is_d else " \\\\ \n"
            return ret_string
        else:
            return ", & "


def latex_old_simplified_formula(a,b,c,d,n_cols):
    assert len(a) == len(b) and len(a) == len(c) and len(a) == len(d)
    N = len(a)
    begin_align = "\\begin{align*}\n"
    end_align =  "\\end{align*}\n"
    empty_line = "&"*(2*n_cols - 1) + " \\\\ \n"
    
    ret_string = ""
    ret_string += begin_align
    ret_string += "x(t) &= \\sum\\limits_{{n=1}}^{{ {} }} ".format(N)
    ret_string += "\\Big[a_n \\cos(2n\\pi t) + b_n \\sin(2n\\pi t) \\Big]\\\\ \n"
    ret_string += "y(t) &= \\sum\\limits_{{n=1}}^{{ {} }} ".format(N)
    ret_string += "\\Big[c_n \\cos(2n\\pi t) + d_n \\sin(2n\\pi t) \\Big]\n"
    ret_string += end_align
    ret_string += "\n"

    ret_string += begin_align
    for letter, coeff_list in [('a', a), ('b', b), ('c', c), ('d', d)]:
        for n in range(N):
            ret_string += "{}_{{ {} }} &= ".format(letter, n+1)
            ret_string += number_to_scientific_latex(coeff_list[n])
            
            ret_string += separator(n, N, n_cols, letter)
        if letter != 'd':
            ret_string += empty_line
    ret_string += end_align
    return ret_string
