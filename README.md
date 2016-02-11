# Full Stack nano degree
### Catalog project

This is the implementaion for item catalog project using Python and sqlite.

To run this project you must have python, sqlite, and vagrant virtual box  installed in your machine.
- First you must create the database using the command from the terminal
    ```
    python database_setup.py
    ```
- Second you can create the categories using the command from the terminal
    ```
    python lots_of_item.py
    ```
    you also can edit this file to add more categories by simply following the steps from the file to write the code needed
- Then you can run the application using this command from the terminal
    ```
    python application.py
    ```
- Open your browser and navigate to http://localhost:8000/

###  Notes and References
- The user who created the item is the only one who can edit or delete this item.
- JSON and XML endpoints routes can be found in the bottom of application.py
- I've used bootstrap css templates and js files from
    http://getbootstrap.com/
- I've used the code for google authentication from the [Authentication and Authorization course](https://www.udacity.com/course/viewer#!/c-ud330-nd) provided by udacity.





