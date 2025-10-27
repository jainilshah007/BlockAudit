import os

def load_knowledge_from_directory(directory_path="knowledge_base"):
    """
    Loads all text-based documents (.txt, .md) from a specified directory
    and all its subdirectories.

    Args:
        directory_path (str): The path to the directory containing knowledge files.

    Returns:
        list of tuples: A list where each tuple contains the relative filepath and its content.
                        Returns None if the directory is not found.
                        Returns an empty list if the directory is empty.
    """
    knowledge_base = []
    print(f"Loading documents from '{directory_path}'...")

    if not os.path.exists(directory_path):
        print(f"Error: Directory not found at '{directory_path}'.")
        print("Please ensure you have downloaded the knowledge files and placed them in the correct directory.")
        return None

    # Use os.walk to recursively traverse all directories and subdirectories
    for root, _, files in os.walk(directory_path):
        if not files and not os.listdir(root): # Check for an initially empty directory
            print(f"Warning: The directory '{directory_path}' appears to be empty.")
            return []
            
        for filename in files:
            # We only consider text-based files
            if filename.endswith((".txt", ".md")):
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        # Store the relative path for better source identification
                        relative_path = os.path.relpath(filepath, directory_path)
                        knowledge_base.append((relative_path, content))
                    print(f"  -> Successfully loaded: {relative_path}")
                except Exception as e:
                    print(f"  -> Error loading {filename}: {e}")
    
    print(f"\nFinished loading. Found {len(knowledge_base)} documents.")
    return knowledge_base

if __name__ == "__main__":
    # This script can be run directly to verify that everything is working correctly.
    loaded_documents = load_knowledge_from_directory()
    
    if loaded_documents is not None:
        print("\n--- Verification ---")
        print(f"Total documents loaded: {len(loaded_documents)}")
        # Display a content snippet from the first document for confirmation
        if loaded_documents:
            first_doc_name, first_doc_content = loaded_documents[0]
            print(f"Content snippet from '{first_doc_name}':")
            print(first_doc_content[:200] + "...")

