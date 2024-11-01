# Define the main function
def calculator():
    # Get the operator from the user
    operator = input("Enter an operator (+, -, *, /): ")

    # Get the operands from the user
    num1 = float(input("Enter the first number: "))
    num2 = float(input("Enter the second number: "))

    # Perform the calculation
    if operator == "+":
        result = num1 + num2
    elif operator == "-":
        result = num1 - num2
    elif operator == "*":
        result = num1 * num2
    elif operator == "/":
        result = num1 / num2
    else:
        print("Invalid operator")

    # Print the result
    print("Result:", result)

# Call the calculator function
calculator()