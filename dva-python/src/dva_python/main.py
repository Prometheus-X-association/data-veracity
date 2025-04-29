import dva_python.logging
import dva_python.msgconsumer


def main():
    dva_python.logging.setup_logging()
    dva_python.msgconsumer.run()



if __name__ == '__main__':
    main()
