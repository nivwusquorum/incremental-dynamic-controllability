from stnu import NamedStnu

def main():
    network = NamedStnu()
    network.read_from_stdin()
    print 'dc' if network.is_dynamically_controllable() else 'notdc'

if __name__ == '__main__':
    main()