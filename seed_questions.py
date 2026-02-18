from app import create_app, db
from app.models import InterviewQuestion

app = create_app()

questions_data = [
    # --- Python & Advanced Programming ---
    {
        "category": "Python",
        "question": "What is the difference between a list and a tuple in Python?",
        "answer": "Lists are mutable (can be changed), while tuples are immutable (read-only). Lists use [], tuples use ().",
        "difficulty": "Easy"
    },
    {
        "category": "Python",
        "question": "Explain List Comprehension in Python.",
        "answer": "It provides a concise way to create lists. Example: [x*x for x in range(10)] creates a list of squares.",
        "difficulty": "Medium"
    },
    {
        "category": "Python",
        "question": "What are Lambda functions?",
        "answer": "Small, anonymous one-line functions defined using the 'lambda' keyword. They can have any number of arguments but only one expression.",
        "difficulty": "Medium"
    },
    {
        "category": "Python",
        "question": "Difference between Shallow and Deep Copy?",
        "answer": "Shallow copy creates a new object but stores references to original elements. Deep copy creates a new object and recursively adds copies of the nested objects.",
        "difficulty": "Hard"
    },

    # --- JavaScript ---
    {
        "category": "JavaScript",
        "question": "What is a 'closure' in JavaScript?",
        "answer": "A closure is a function that remembers and has access to its lexical scope even when that function is executing outside its original scope.",
        "difficulty": "Medium"
    },
    {
        "category": "JavaScript",
        "question": "Difference between var, let, and const?",
        "answer": "var is function-scoped. let and const are block-scoped. const variables cannot be reassigned once defined.",
        "difficulty": "Easy"
    },
    {
        "category": "JavaScript",
        "question": "Explain Promises in JavaScript.",
        "answer": "A Promise represents a value that may be available now, in the future, or never. It's used for handling asynchronous operations like API calls.",
        "difficulty": "Medium"
    },
    {
        "category": "JavaScript",
        "question": "What is 'Hoisting'?",
        "answer": "JavaScript moves variable and function declarations to the top of their scope before code execution. Only declarations are hoisted, not initializations.",
        "difficulty": "Medium"
    },

    # --- SQL (NEW) ---
    {
        "category": "SQL",
        "question": "What are Joins in SQL?",
        "answer": "Joins combine rows from two or more tables based on a related column. Types: Inner (common rows), Left (all left rows + matches), Right (all right rows + matches), and Full (all rows).",
        "difficulty": "Medium"
    },
    {
        "category": "SQL",
        "question": "Primary Key vs Foreign Key?",
        "answer": "A Primary Key uniquely identifies a record in a table and cannot be null. A Foreign Key is a column in one table that refers to the Primary Key of another table.",
        "difficulty": "Easy"
    },
    {
        "category": "SQL",
        "question": "What is Database Indexing?",
        "answer": "Indexing is a technique to speed up data retrieval by creating pointers to data location, similar to a book's index. It speeds up SELECTs but can slow down INSERTs.",
        "difficulty": "Medium"
    },
    {
        "category": "SQL",
        "question": "DELETE vs TRUNCATE vs DROP?",
        "answer": "DELETE removes specific rows (log-based, rollable). TRUNCATE removes all rows (faster, can't rollback). DROP deletes the entire table structure.",
        "difficulty": "Hard"
    },

    # --- Web Development (NEW) ---
    {
        "category": "Web Dev",
        "question": "Difference between HTTP and HTTPS?",
        "answer": "HTTP is standard unencrypted data transfer. HTTPS is HTTP with SSL/TLS encryption, ensuring secure data exchange between the browser and server.",
        "difficulty": "Easy"
    },
    {
        "category": "Web Dev",
        "question": "What are REST APIs?",
        "answer": "REST (Representational State Transfer) is an architectural style for designing networked applications using standard HTTP methods (GET, POST, PUT, DELETE).",
        "difficulty": "Medium"
    },
    {
        "category": "Web Dev",
        "question": "Cookies vs LocalStorage?",
        "answer": "Cookies are small (4KB), sent to server with every request, and have expiration. LocalStorage is larger (5-10MB), stays on client only, and never expires unless deleted.",
        "difficulty": "Medium"
    },

    # --- Security (NEW) ---
    {
        "category": "Security",
        "question": "What is SQL Injection?",
        "answer": "A cyber-attack where malicious SQL code is inserted into input fields to manipulate backend databases. Prevented by using Parameterized Queries (Prepared Statements).",
        "difficulty": "Medium"
    },
    {
        "category": "Security",
        "question": "Explain XSS (Cross-Site Scripting).",
        "answer": "An attack where malicious scripts are injected into web pages viewed by other users. Can be used to steal session cookies or user data.",
        "difficulty": "Hard"
    },

    # --- DSA (Data Structures & Algorithms) ---
    {
        "category": "DSA",
        "question": "What is a linear data structure?",
        "answer": "A linear data structure organizes elements sequentially. Key examples include Arrays, Linked Lists, and Stacks.",
        "difficulty": "Easy"
    },
    {
        "category": "DSA",
        "question": "Explain Stack (LIFO) vs Queue (FIFO).",
        "answer": "Stacks follow Last-In-First-Out (LIFO). Queues follow First-In-First-Out (FIFO). Used in recurison and task scheduling respectively.",
        "difficulty": "Easy"
    },
    {
        "category": "DSA",
        "question": "Array vs Linked List Trade-offs?",
        "answer": "Arrays allow fast random access O(1) but slow insertion O(n). Linked Lists allow fast insertion O(1) but slow access O(n).",
        "difficulty": "Medium"
    },
    {
        "category": "DSA",
        "question": "How does Binary Search work?",
        "answer": "Used on sorted arrays only. It repeatedly divides the search range in half, achieving O(log n) efficiency compared to Linear Search's O(n).",
        "difficulty": "Medium"
    },
    {
        "category": "DSA",
        "question": "Quick Sort vs Merge Sort?",
        "answer": "Quick Sort is typically faster in-place but has O(n^2) worst case. Merge Sort is stable with O(n log n) always, but requires extra space.",
        "difficulty": "Hard"
    },

    # --- Networking ---
    {
        "category": "Networking",
        "question": "What is DNS?",
        "answer": "DNS (Domain Name System) acts as the phonebook of the internet, translating human-readable names like 'google.com' into machine IP addresses.",
        "difficulty": "Easy"
    },
    {
        "category": "Networking",
        "question": "TCP vs UDP?",
        "answer": "TCP is connection-oriented, ensuring reliable data delivery (slower). UDP is connectionless, prioritizing speed over reliability (e.g., video streaming).",
        "difficulty": "Medium"
    },
    {
        "category": "Networking",
        "question": "What happens when you type a URL in browser?",
        "answer": "DNS lookup -> Request sent -> Server processes -> Browser renders. Steps include IP resolution, TCP/SSL handshake, and HTTP GET request.",
        "difficulty": "Hard"
    },

    # --- OS (Operating Systems) ---
    {
        "category": "OS",
        "question": "What is a Process vs a Thread?",
        "answer": "A Process is an independent program in execution with its own memory. A Thread is a subset of a process that shares memory with other threads in the same process.",
        "difficulty": "Medium"
    },
    {
        "category": "OS",
        "question": "What is a Deadlock?",
        "answer": "A situation where two or more processes are blocked forever, each waiting for a resource held by the other. Conditions: Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait.",
        "difficulty": "Hard"
    },
    {
        "category": "OS",
        "question": "Virtual Memory concept?",
        "answer": "A memory management technique that uses hardware and software to allow a computer to compensate for physical memory shortages by temporarily transferring data from RAM to disk storage.",
        "difficulty": "Hard"
    },

    # --- OOPs (Object Oriented Programming) ---
    {
        "category": "OOPs",
        "question": "Difference between Abstract Class and Interface?",
        "answer": "Abstract classes can have both concrete and abstract methods and state. Interfaces (in Java/C#) mostly define method signatures that must be implemented.",
        "difficulty": "Medium"
    },
    {
        "category": "OOPs",
        "question": "Explain Encapsulation.",
        "answer": "The bundling of data and methods that operate on that data within a single unit (class), while restricting direct access to some of the object's components.",
        "difficulty": "Easy"
    },

    # --- Java ---
    {
        "category": "Java",
        "question": "What is the JVM (Java Virtual Machine)?",
        "answer": "JVM is an engine that provides a runtime environment to drive Java Code or applications. It converts Java bytecode into machine language.",
        "difficulty": "Easy"
    },
    {
        "category": "Java",
        "question": "Final vs Finally vs Finalize?",
        "answer": "Final is a keyword (restrict modification). Finally is a block (execution after try-catch). Finalize is a method (cleanup before garbage collection).",
        "difficulty": "Medium"
    },
    {
        "category": "Java",
        "question": "What is Garbage Collection?",
        "answer": "Automated memory management that identifies and deletes objects that are no longer being used by the program to reclaim heap memory.",
        "difficulty": "Medium"
    },

    # --- DBMS ---
    {
        "category": "DBMS",
        "question": "What are Database Tiers?",
        "answer": "Categorization of DB architecture. 1-Tier (Embedded), 2-Tier (Client-Server), 3-Tier (Client-Web Server-DB Server).",
        "difficulty": "Medium"
    },
    {
        "category": "DBMS",
        "question": "Explain Normalization.",
        "answer": "Process of organizing data in a database to reduce redundancy and improve data integrity by dividing large tables into smaller, related ones.",
        "difficulty": "Hard"
    },

    # --- General Tech & Tools ---
    {
        "category": "General Tech",
        "question": "What is Git and GitHub?",
        "answer": "Git is a local version control system. GitHub is a cloud-based hosting service for Git repositories, allowing for team collaboration.",
        "difficulty": "Easy"
    },
    {
        "category": "General Tech",
        "question": "Explain Agile Methodology.",
        "answer": "An iterative approach to software development and project management that helps teams deliver value to customers faster and with fewer headaches.",
        "difficulty": "Medium"
    },

    # --- HR & Behavioral ---
    {
        "category": "HR",
        "question": "How do you handle conflict in a team?",
        "answer": "Focus on communication, listening to all sides fairly, remaining objective, and working towards a solution that benefits the project goals.",
        "difficulty": "Medium"
    },
    {
        "category": "HR",
        "question": "What is your biggest achievement?",
        "answer": "Select a professional or academic accomplishment where you overcame a challenge, used specific skills, and delivered a measurable positive outcome.",
        "difficulty": "Medium"
    },
    {
        "category": "HR",
        "question": "Where do you see yourself in 5 years?",
        "answer": "Show ambition by mentioning your desire to gain deeper expertise, lead projects, or take on more responsibility within the company.",
        "difficulty": "Easy"
    }
]

def seed_data():
    with app.app_context():
        # Clear existing questions to ensure the database perfectly matches the script categorization
        InterviewQuestion.query.delete() 
        
        for q in questions_data:
            question = InterviewQuestion(
                    category=q["category"],
                    question=q["question"],
                    answer=q["answer"],
                    difficulty=q["difficulty"]
                )
            db.session.add(question)
        
        db.session.commit()
        print("Successfully seeded interview questions!")

if __name__ == "__main__":
    seed_data()
