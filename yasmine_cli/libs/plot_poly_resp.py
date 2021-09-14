
from obspy.core.inventory.response import PolynomialResponseStage, InstrumentPolynomial
import matplotlib.pyplot as plt
import os
import numpy as np

def plot_polynomial_resp(response, label=None, axes=None, outfile=None,
                         vmin=-20., vmax=20., dv=0.10):
    """
    Plot polynomial response
        The way that polynomial responses are calculated is a bit "bassackwards":
        Given a range of inputs (e.g., temperatures), we use the polynomial coefficients
        to calculate what the corresponding outputs (volts or counts) would be.
        We plot input_units on the x-axis and output_units on the y-axis to form y=y(x).

        Will produce 2 subplots: 1. xy-plot of y=output_units (e.g., Volts) vs x=input_units (e.g., degC)
                                 2. xy-plot of y=output_units (e.g., Counts)vs x=input_units (e.g., degC)

        For a MCLAUREN polynomial response, plot 1 comes from the PolynomialResponseStage (e.g., first stage)
              while plot 2 comes from the InstrumentPolynomial (overall response with net gain included in coeffs)

    :param response: channel polynomial response
    :type output: ObsPy response object

    MTH: By default, plot_polynomial_resp will step over voltage from -20V to +20V
         with dV step=0.1V, but the final plot xy ranges will be set by
         the input (x-axis) range: poly.approximation_lower_bound - upper_bound
         However, I left vmin/vmax/dv configurable in case a calling function wants
         to control this to limit plot range (somehow).
    """

    if not response.instrument_polynomial or not isinstance(response.response_stages[0], PolynomialResponseStage):
        logger.error("plot_polynomial_resp: response does not contain instrument_polynomial ",
                     "and/or PolynomialResponseStage")
        return None

    #file_name = outfile
    #os.makedirs(folder, exist_ok=True)
    #sanitized_file_name = file_name.replace('/', '_').replace('\\', '_') + '.png'
    #file_path = os.path.join(folder, f'{sanitized_file_name}')
    #outfile = file_path

    # We'll use the overall gain to scale between Volts and Counts
    net_gain = 1.
    for i, stage in enumerate(response.response_stages):
        if stage.stage_gain:
            net_gain *= stage.stage_gain

    poly = response.response_stages[0]
    xlabel = poly.input_units
    ylabel = poly.output_units

    # MTH: We need a min/max in the *output* space (e.g., volts) to step through
    #      Otherwise we'll be calculating wild values out of range
    #      Add a little bit to vmax to it gets included in the array
    volts = np.arange(vmin, vmax+dv/10., dv)

    # Load x=temp = f(y=volts) // the measured thing might not be "temp", it doesn't matter
    x1 = []
    y1 = []
    for volt in volts:
        temp = 0.
        for i, c in enumerate(poly.coefficients):
            temp += c * np.power(volt, i)
        if temp >= poly.approximation_lower_bound and temp <= poly.approximation_upper_bound:
            # print("V:%.3f     T:%.2f" % (volt, temp))
            x1.append(temp)
            y1.append(volt)

    # Load x=temp = f(y=counts)
    poly = response.instrument_polynomial
    y2label = poly.output_units
    x2 = []
    y2 = []
    print()
    for volt in volts:
        temp = 0.
        count = volt * net_gain
        for i, c in enumerate(poly.coefficients):
            temp += c * np.power(count, i)
        if temp >= poly.approximation_lower_bound and temp <= poly.approximation_upper_bound:
            # print("C:%.3f     T:%.2f" % (count, temp))
            x2.append(temp)
            y2.append(count)

    if axes:
        ax1, ax2 = axes
        fig = ax1.figure
    else:
        fig = plt.figure()
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212, sharex=ax1)

    label_kwarg = {}
    # if label is not None:
    #   label_kwarg['label'] = label

    plt.suptitle(label)
    plt.xlabel(xlabel)
    ax1.set_ylabel(ylabel)
    ax2.set_ylabel(y2label)
    ax2.ticklabel_format(axis='y', style='sci', useMathText=True, scilimits=(0, 0))

    lw = 1.5
    marker = "."
    color = 'red'
    lines = ax1.plot(x1, y1, marker=marker, color=color, **label_kwarg)

    # color = lines[0].get_color()
    lines = ax2.plot(x2, y2, color=color, marker=marker)

    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.3)

    show = 1
    if outfile:
        fig.savefig(outfile)
    else:
        if show:
            plt.show()

    return fig
    #return sanitized_file_name


