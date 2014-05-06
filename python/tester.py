from stnu import NamedStnu
from fast_dc import DcTester

def main():
    network = NamedStnu()
    network.read_from_stdin()
    dc_tester = DcTester(network)
    print 'dc' if dc_tester.is_dynamically_controllable() else 'notdc'

if __name__ == '__main__':
    main()