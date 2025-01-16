
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import random
from tkcalendar import DateEntry

class TaskPickerApp:
   
    
    def __init__(self, root):
        self.root = root
        self.root.title("Task Picker App")
        self.root.geometry("800x600")
        
        # Initialize database
        self.init_database()
        
        # Create main container
        self.main_container = ttk.Frame(self.root, padding="10")
        self.main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Add theme support (move this before creating UI elements)
        self.theme_var = tk.StringVar(value="light")
        
        # Initialize categories
        self.categories = ['Work', 'Personal', 'Study', 'Health', 'Other']
        
        # Create UI elements
        self.create_task_input_section()
        self.create_task_list_section()
        self.create_task_picker_section()
        
        # Setup theme (after creating UI elements)
        self.setup_theme()
        
    def init_database(self):
        """Initialize SQLite database and create tables if they don't exist"""
        self.conn = sqlite3.connect('taskpicker.db')
        self.cursor = self.conn.cursor()
        
        # Create tasks table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                priority_level TEXT,
                deadline DATE,
                category TEXT,
                completed_status BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
        
    def create_task_input_section(self):
        """Create the section for adding new tasks"""
        input_frame = ttk.LabelFrame(self.main_container, text="Add New Task", padding="5")
        input_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Task name input (row 0)
        ttk.Label(input_frame, text="Task:").grid(row=0, column=0, padx=5)
        self.task_entry = ttk.Entry(input_frame, width=40)
        self.task_entry.grid(row=0, column=1, padx=5)
        
        # Priority dropdown (row 0)
        ttk.Label(input_frame, text="Priority:").grid(row=0, column=2, padx=5)
        self.priority_var = tk.StringVar()
        priority_combo = ttk.Combobox(input_frame, textvariable=self.priority_var)
        priority_combo['values'] = ('High', 'Medium', 'Low')
        priority_combo.grid(row=0, column=3, padx=5)
        
        # Category dropdown (row 1)
        ttk.Label(input_frame, text="Category:").grid(row=1, column=0, padx=5, pady=5)
        self.category_var = tk.StringVar()
        category_combo = ttk.Combobox(input_frame, textvariable=self.category_var)
        category_combo['values'] = self.categories
        category_combo.grid(row=1, column=1, padx=5, pady=5)
        
        # Deadline picker (row 1)
        ttk.Label(input_frame, text="Deadline:").grid(row=1, column=2, padx=5)
        self.deadline_picker = DateEntry(input_frame, width=12, background='darkblue',
                                       foreground='white', borderwidth=2)
        self.deadline_picker.grid(row=1, column=3, padx=5)
        
        # Add task button (row 1)
        ttk.Button(input_frame, text="Add Task", command=self.add_task).grid(row=1, column=4, padx=5)
        
    def create_task_list_section(self):
        """Create the section for displaying tasks"""
        list_frame = ttk.LabelFrame(self.main_container, text="Task List", padding="5")
        list_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Filter frame
        filter_frame = ttk.Frame(list_frame)
        filter_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Category filter
        ttk.Label(filter_frame, text="Filter by:").pack(side=tk.LEFT, padx=5)
        self.filter_category = tk.StringVar()
        category_filter = ttk.Combobox(filter_frame, textvariable=self.filter_category, width=15)
        category_filter['values'] = ['All'] + self.categories
        category_filter.set('All')
        category_filter.pack(side=tk.LEFT, padx=5)
        category_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_task_list())
        
        # Create treeview for tasks
        self.task_tree = ttk.Treeview(list_frame, columns=('Task', 'Priority', 'Category', 'Deadline', 'Status'))
        self.task_tree.heading('Task', text='Task')
        self.task_tree.heading('Priority', text='Priority')
        self.task_tree.heading('Category', text='Category')
        self.task_tree.heading('Deadline', text='Deadline')
        self.task_tree.heading('Status', text='Status')
        
        # Configure column widths
        self.task_tree.column('Task', width=200)
        self.task_tree.column('Priority', width=70)
        self.task_tree.column('Category', width=100)
        self.task_tree.column('Deadline', width=100)
        self.task_tree.column('Status', width=70)
        
        self.task_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind double-click event for marking tasks as complete
        self.task_tree.bind('<Double-1>', self.toggle_task_completion)
        
    def create_task_picker_section(self):
        """Create the section for picking random tasks"""
        picker_frame = ttk.LabelFrame(self.main_container, text="Task Picker", padding="5")
        picker_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(picker_frame, text="Pick Random Task", command=self.pick_random_task).grid(row=0, column=0, padx=5)
        self.picked_task_label = ttk.Label(picker_frame, text="")
        self.picked_task_label.grid(row=0, column=1, padx=5)
        
    def add_task(self):
        """Add a new task to the database"""
        task_name = self.task_entry.get()
        priority = self.priority_var.get()
        category = self.category_var.get()
        deadline = self.deadline_picker.get_date()
        
        if not task_name:
            messagebox.showwarning("Warning", "Please enter a task name!")
            return
            
        self.cursor.execute('''
            INSERT INTO tasks (task_name, priority_level, category, deadline)
            VALUES (?, ?, ?, ?)
        ''', (task_name, priority, category, deadline))
        self.conn.commit()
        
        self.task_entry.delete(0, tk.END)
        self.priority_var.set('')
        self.category_var.set('')
        self.refresh_task_list()
        
    def refresh_task_list(self):
        """Refresh the task list display with optional filtering"""
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
            
        query = '''
            SELECT task_name, priority_level, category, deadline, completed_status 
            FROM tasks
        '''
        
        if self.filter_category.get() != 'All':
            query += ' WHERE category = ?'
            self.cursor.execute(query, (self.filter_category.get(),))
        else:
            self.cursor.execute(query)
            
        for task in self.cursor.fetchall():
            status = "✓" if task[4] else "○"
            deadline_str = datetime.strptime(task[3], '%Y-%m-%d').strftime('%Y-%m-%d') if task[3] else ''
            self.task_tree.insert('', tk.END, values=(task[0], task[1], task[2], deadline_str, status))
            
    def toggle_task_completion(self, event):
        """Toggle the completion status of a task"""
        selected_item = self.task_tree.selection()
        if not selected_item:
            return
            
        task_name = self.task_tree.item(selected_item)['values'][0]
        
        self.cursor.execute('''
            UPDATE tasks 
            SET completed_status = NOT completed_status 
            WHERE task_name = ?
        ''', (task_name,))
        self.conn.commit()
        self.refresh_task_list()
        
    def setup_theme(self):
        """Setup theme selection and initial styles"""
        theme_frame = ttk.Frame(self.main_container)
        theme_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.E), pady=5)
        
        # Create and configure styles
        self.style = ttk.Style()
        
        # Configure initial light theme
        self.configure_theme_styles("light")
        
        ttk.Label(theme_frame, text="Theme:").pack(side=tk.LEFT, padx=5)
        theme_switch = ttk.Checkbutton(theme_frame, text="Dark Mode",
                                     command=self.toggle_theme,
                                     variable=self.theme_var,
                                     onvalue="dark", offvalue="light")
        theme_switch.pack(side=tk.LEFT)

    def configure_theme_styles(self, theme):
        """Configure styles for all widgets based on theme"""
        if theme == "dark":
            # Dark theme colors
            bg_color = '#2b2b2b'
            fg_color = '#ffffff'
            select_bg = '#404040'
            # Darker input and tree backgrounds for better contrast
            tree_bg = '#1e1e1e'  # Darker background for tree
            input_bg = '#1e1e1e'  # Darker background for input fields
            frame_bg = '#363636'
        else:
            # Light theme colors
            bg_color = '#f0f0f0'
            fg_color = '#000000'
            select_bg = '#0078d7'
            tree_bg = '#ffffff'
            input_bg = '#ffffff'
            frame_bg = '#f5f5f5'

        # Configure main window
        self.root.configure(bg=bg_color)
        
        # Configure styles for different widget types
        self.style.configure("TFrame", background=bg_color)
        self.style.configure("TLabel", background=bg_color, foreground=fg_color)
        self.style.configure("TButton", 
                            background=bg_color, 
                            foreground=fg_color,
                            focuscolor=select_bg)
        
        # LabelFrame style
        self.style.configure("TLabelframe", 
                            background=frame_bg,
                            foreground=fg_color)
        self.style.configure("TLabelframe.Label", 
                            background=frame_bg,
                            foreground=fg_color)
        
        # Entry style
        self.style.configure("TEntry", 
                            fieldbackground=input_bg,
                            foreground=fg_color,
                            selectbackground=select_bg,
                            selectforeground=fg_color)
        
        # Combobox style
        self.style.configure("TCombobox", 
                            fieldbackground=input_bg,
                            background=input_bg,
                            foreground=fg_color,
                            selectbackground=select_bg,
                            selectforeground=fg_color)
        
        # Treeview style
        self.style.configure("Treeview",
                            background=tree_bg,
                            foreground=fg_color,
                            fieldbackground=tree_bg)
        self.style.configure("Treeview.Heading",
                            background=frame_bg,
                            foreground=fg_color)
        self.style.map("Treeview",
                       background=[('selected', select_bg)],
                       foreground=[('selected', '#ffffff')])
        
        # Update DateEntry colors
        if hasattr(self, 'deadline_picker'):
            self.deadline_picker.configure(
                background=select_bg if theme == "dark" else 'darkblue',
                foreground='white',
                selectbackground=select_bg,
                selectforeground='white'
            )

    def toggle_theme(self):
        """Toggle between light and dark theme"""
        theme = self.theme_var.get()
        self.configure_theme_styles(theme)
        
    def pick_random_task(self):
        """Pick a random task from the incomplete tasks"""
        self.cursor.execute('SELECT task_name FROM tasks WHERE completed_status = 0')
        tasks = self.cursor.fetchall()
        if tasks:
            random_task = random.choice(tasks)[0]
            self.picked_task_label.config(text=f"Selected Task: {random_task}")
        else:
            self.picked_task_label.config(text="No tasks available!")

def main():
    """Entry point of the application"""
    root = tk.Tk()
    app = TaskPickerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
