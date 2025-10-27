from solidity_parser import parser

def parse_solidity_code(code_snippet):
    """
    Parses a Solidity code snippet and extracts all function definitions.

    Args:
        code_snippet (str): The string containing the Solidity code.

    Returns:
        list of dicts: A list where each dictionary contains the name and body of a function.
                       Returns the full snippet as a single item if parsing fails.
    """
    functions = []
    try:
        # Parse the code into an Abstract Syntax Tree (AST)
        ast = parser.parse(code_snippet, loc=False)
        
        # Traverse the AST to find all function definitions
        for node in ast.get('children', []):
            if node.get('type') == 'ContractDefinition':
                for sub_node in node.get('subNodes', []):
                    if sub_node.get('type') == 'FunctionDefinition':
                        function_name = sub_node.get('name')
                        if function_name:
                             # For a more precise analysis, we send the full code along with the function name
                             # to provide complete context to the LLM.
                            functions.append({
                                "name": function_name,
                                "code": code_snippet 
                            })
        
        # If no functions are found (e.g., user submitted a single line or a question)
        # return the entire input for analysis.
        if not functions:
            return [{"name": "Full Snippet Analysis", "code": code_snippet}]
            
        return functions
    except Exception as e:
        print(f"Warning: Error parsing Solidity code: {e}")
        # If parsing fails for any reason, fall back to analyzing the full code snippet.
        return [{"name": "Full Snippet Analysis", "code": code_snippet}]

if __name__ == "__main__":
    # An example to test the parser directly
    sample_code = """
    contract Simple {
        function safeAdd(uint a, uint b) public pure returns (uint) {
            return a + b;
        }

        function unsafeWithdraw() public {
            // vulnerable code
        }
    }
    """
    parsed_functions = parse_solidity_code(sample_code)
    print("Parsed Functions:")
    for func in parsed_functions:
        print(f"- {func['name']}")

