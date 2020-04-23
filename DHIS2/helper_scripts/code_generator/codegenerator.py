import subprocess


def main():
    number = 50
    while number > 0:
        get_code()
        number = number -1

def get_code():
    command = "java CodeGenerator"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    print(str(output).replace("b'", "").replace("\\n'", ""))


if __name__ == '__main__':
    main()