import numpy
import pytest
from .window_main import WindowMain

def test_main():
    #args = get_parser().parse_args()
    #print(args)

    app = QApplication(sys.argv)
    #win = WindowMain(args.host, args.port, args.timeout, args.sig,
    #                 args.axis, args.sigset, args.corr, args.yrange)
    win = WindowMain("w-kitslab-icepap-21", 5000, 3, [],
                     1, "", "", "")
    '''
    sig_set = [
        '1:PosAxis:1',
        '1:PosAbsenc:1',
        '1:PosInpos:1',
        '1:PosEncin:1',
    ]
    win = WindowMain("w-kitslab-icepap-21", 5000, 3, sig_set,
                     1, "", "", "")
    axis_aux = 2
    win = WindowMain("w-kitslab-icepap-21", 5000, 3, sig_set,
                     axis_aux, "", "", "")
    sigset_file = "sigset.lst"
    win = WindowMain("w-kitslab-icepap-21", 5000, 3, sig_set,
                     1, sigset_file, "", "")
    sigset_file = "sigset.lst"
    corr_factors_test = [2, 1000, 3 10000]
    win = WindowMain("w-kitslab-icepap-21", 5000, 3, sig_set,
                     1, sigset_file, corr_factors_test, "")
    '''
    win.show()
    sys.exit(app.exec_())

