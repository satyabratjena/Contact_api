- Contact Application 
************************
--- This API provides endpoints to manage contacts in a contact management system. It allows creating, reading, updating, and deleting contact records.

# start.py is the single file containing all the information(table and apis)

## I tried to do it differently but getting some Import Module Error, so compile all the information to a single file.

--- to interact with database I have initiated a connection with the postgresql

-- The base URL for all API endpoints is http://localhost:5000/

API ENDPOINTS
***************

# GET
-> GET /get - for getting all the contacts
-> GET /<contact_id> - for getting sinlge contact
-> query parameters: order_by, sort, search by name, email, mobile number, pagination

# POST
-> POST /create - Accepting the JSON payload with details, can create a single contact or multiple contacts in the database, for bulk contact insertion, provide a JSON array with multiple contact objects.

# PUT
-> PUT /updates -> for updating by JSON payload with contact details
-> PUT /<contact_id> -> for updating single contact

-> DELETE /delete -> for deleting by JSON payload giving contact IDs

# Below apis have not been tested its giving an error message
-> DELETE /<contact_id>
-> DELETE /name/<name> -> sometime we have different name sig
-> DELETE /address/<address> -> for deleting contacts for a specific address/area

# Error Handling 

-> Exception - normal exceptionq and logs the error
-> ContactException - it handles custom contact related exception 
-> SQLAlchemyError - it handles SQLAlchemy related exception

