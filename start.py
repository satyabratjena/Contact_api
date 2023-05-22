from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from dataclasses import dataclass


from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_

import logging
import os


app = Flask(__name__)

app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql+psycopg2://satya:satyabrat@localhost/app"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy(app)


# Below is the database tables
@dataclass
class Contact(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.Text, nullable=False)
    email: str = db.Column(db.String(255), nullable=False)
    gender: str = db.Column(db.String(1), nullable=False)
    mobile: str = db.Column(db.String(10), nullable=False)
    address: str = db.Column(db.String, nullable=False)


app.app_context().push()
db.create_all()
db.session.commit()


# Create exceptions
class ContactException(Exception):
    def __init__(self, message, code=400):
        self.message = message
        self.code = code


@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.exception(e)
    return {"success": False, "error": str(e)}, 400


@app.errorhandler(ContactException)
def handle_sheduler_exception(e):
    app.logger.exception(e)
    return {"success": False, "error": f"{e.message}"}, e.code


@app.errorhandler(SQLAlchemyError)
def handle_sql_exception(e):
    app.logger.exception(e)
    return {"success": False, "error": f"{e.orig}"}, 400


# <<<<<<<<<<<<<<<<<<<<   Contact APIs >>>>>>>>>>>>>>>>>>>>>>>


# Below code is for getting the contacts
@app.route("/get", methods=["GET"])
@app.route("/<contact_id>", methods=["GET"])
def get_details(contacts_id=None):
    order = request.args.get("order", "asc", "desc")
    sort = request.args.get("sort", "name")
    search = request.args.get("search")
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=5, type=int)
    pagination = Contact.query.order_by(
        getattr(Contact, sort).asc()
        if order == "asc"
        else getattr(Contact, sort).desc()
    ).paginate(page, per_page, False)

    details = Contact.query

    if contacts_id:
        details = details.filter(Contact.id == Contact.contacts_id)
        if not details:
            raise ContactException(f"{contacts_id} id does not exist", 404)

    # Below code is for ascending and descending order(do check if these are working)
    if order == "asc":
        details = details.order_by(getattr(Contact, sort).asc())
    else:
        details = details.order_by(getattr(Contact, sort).desc())

    # Below is for searching, do see if these are working fine or not(should be able search by different column)
    if search:
        details = details.filter(Contact.name.ilike(f"%{search}%"))
        details = details.filter(Contact.email.ilike(f"%{search}%"))
        details = details.filter(Contact.mobile.ilike(f"%{search}%"))

        # Below is for pagination
    contacts = Contact.query.order_by(Contact.name).paginate(page, per_page)

    contact_details = [contact.to_dict() for contact in contacts.item]

    return {
        "contacts": contact_details,
        "sort": sort,
        "order": order,
        "current_page": details.page,
        "per_page": per_page,
        "total pages": details.pages,
        "total_contacts": details.total,
        "message": "contact details retrived successfully",
    }


# Below code is for Creating contact
@app.route("/create", methods=["POST"])
def add_contact(
    name=None,
    email=None,
    gender=None,
    mobile=None,
    address=None,
):
    data = request.json

    # Adding single contact
    if type(data) == dict:
        name = name or request.json.get("name")
        email = email or request.json.get("email")
        gender = gender or request.json.get("gender")
        mobile = mobile or request.json.get("mobile")
        address = address or request.json.get("address")

        existing_contact = Contact.query.filter_by(name=name).first()

        if existing_contact:
            raise ContactException(
                f"Contact name'{existing_contact.name}'already exists."
            )

        try:
            contact = Contact(
                name=name,
                email=email,
                gender=gender,
                mobile=mobile,
                address=address,
            )
            db.session.add(contact)
            db.session.commit()
            return {
                "success": True,
                "message": f"Contact {contact.name} added successfully.",
            }, 201

        except IntegrityError as e:
            assert isinstance(e.orig, UniqueViolation)
            db.session.rollback()
            return {"status": False, "error": f"Contact name'{name}'already exists."}

    else:
        # Adding contacts to the database in bulk,
        for item in data:
            name = item.get("name")
            email = item.get("email")
            gender = item.get("gender")
            mobile = item.get("mobile")
            address = item.get("address")

            try:
                contact = Contact(
                    name=name,
                    email=email,
                    gender=gender,
                    mobile=mobile,
                    address=address,
                )
                db.session.add(contact)
                db.session.commit()
                return {
                    "success": True,
                    "message": f"Contact {name} added successfully.",
                }, 201
            except IntegrityError as e:
                assert isinstance(e.orig, UniqueViolation)
                db.session.rollback()
                return {
                    "status": False,
                    "error": f"Contact name'{name}'already exists.",
                }


# Below code is for updating the data
@app.route("/updates", methods=["PUT"])
@app.route("/<contact_id>", methods=["PUT"])
def update_contact(id):
    contact = Contact.query.filter_by(id=id).first()

    if not contact:
        raise ContactException("Contact id does not present in Database")

    contact.name = contact.name or request.json.get("name")
    contact.email = contact.email or request.json.get("email")
    contact.mobile = contact.mobile or request.json.get("mobile")
    contact.address = contact.address or request.json.get("address")

    db.session.add(contact)
    db.session.commit()


@app.route("/updates", methods=["PUT"])
def update_bulk_contact():
    data = request.json
    if not data:
        raise ContactException("No contact Data found.", 404)
    for contacts in data:
        user = contacts.get("id")

        if not user:
            raise ContactException("No contact Data found.", 404)

        contact = Contact.query.filter_by(id=user).first()

        if not contact:
            return {"status": False, "message": f"{user} not found for the given id"}

        contacts.name = contacts.get("name", contacts.name)
        contacts.email = contacts.get("email")
        contacts.mobile = contacts.get("mobile")
        contacts.address = contacts.get("address")

        db.session.add(contact)
    db.session.commit()

    return {
        "status": True,
        "message": "Data updated for all the given contacts",
        "contacts": data,
    }, 200


# Below code is for deleting the data
# instead of writing the endpoint define different function.
@app.route("/delete", methods=["DELETE"])
def delete_contact():
    contact_list = request.json

    if contact_list:
        data = request.json.get("Contact_Ids")
        if data is None:
            raise ContactException(f"No contacts found", 404)
        for contact_id in data:
            contact = Contact.query.filter_by(contact_id)
            db.session.delete(contact)
    db.session.commit()
    return {"success": True, "message": "Contact deleted successfully"}


# Deletion for particular id
@app.route("/<contact_id>", methods=["DELETE"])
def delete_contact_by_id(contact_id):
    contact = Contact.query.get(contact_id)
    if contact:
        db.session.delete(contact)
        db.session.commit()
        return {"success": True, "message": "Contact deleted successfully"}
    else:
        raise ContactException(f"Contact with ID '{contact_id}' not found", 404)


# Deletion by giving address
@app.route("/address/<address>", methods=["DELETE"])
def delete_contact_by_address(address):
    contact = Contact.query.filter_by(address=address).first()
    if contact:
        db.session.delete(contact)
        db.session.commit()
        return {"success": True, "message": "Contact deleted successfully"}
    else:
        raise ContactException(f"Contact with address '{address}' not found", 404)


if __name__ == "__main__":
    app.run(debug=True)
