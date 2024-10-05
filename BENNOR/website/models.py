from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from datetime import datetime

class Users7(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    role = db.Column(db.String(50))
    past_experience = db.Column(db.String)
    last_profile_update = db.Column(db.DateTime, nullable=True)
    notes = db.relationship('Note')
    events = db.relationship('Events15')
    attend = db.relationship('Attendee_events7')
    client_events = db.relationship('Client_events6')
    supplier_info8 = db.relationship('Supplier_info8')
    # New credibility columns
    credibility1 = db.Column(db.String(300), nullable=True)
    credibility2 = db.Column(db.String(300), nullable=True)
    credibility3 = db.Column(db.String(300), nullable=True)
    credibility4 = db.Column(db.String(300), nullable=True)
    credibility5 = db.Column(db.String(300), nullable=True)


class Events15(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data1 = db.Column(db.String)  # Store data as JSON string
    room_code = db.Column(db.String)
    event_name = db.Column(db.String)
    event_desc = db.Column(db.String)  # New column for event description
    event_type = db.Column(db.String)
    event_privacy = db.Column(db.String)  # New column for event status
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users7.id'))
    invited_attendees = db.Column(db.Text)
    rsvp_attendees = db.Column(db.String)
    max_attendee_num = db.Column(db.Integer)  # New column for max attendees
    selected_suppliers = db.Column(db.String)
    start_date = db.Column(db.DateTime)  # New column for start time/date
    end_date = db.Column(db.DateTime)  # New column for end time/date


class HiredSuppliers3(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events15.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users7.id'), nullable=False)  # Link to the user who accepted the request
    supplier_fullname = db.Column(db.String, nullable=False)
    supplier_type = db.Column(db.String, nullable=False)
    commission = db.Column(db.String, nullable=False)
    phone_number = db.Column(db.Integer, nullable=False)
    phone_number2 = db.Column(db.Integer, nullable=True)
    email_sup = db.Column(db.String, nullable=False)
    supplier_description = db.Column(db.String, nullable=True)
    extra_info = db.Column(db.String, nullable=True)
    over_all_rating = db.Column(db.String, nullable=True)

    event = db.relationship('Events15', backref='hired_suppliers')
    user = db.relationship('Users7', backref='hired_suppliers')  # Backref to Users7


class Attendee_events7(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invites = db.Column(db.Text)  # Store data as JSON string
    rsvp_events = db.Column(db.Text)
    attending_events = db.Column(db.Text)
    rejected_invites = db.Column(db.Text)  # New column to store rejected invites and reasons
    user_id = db.Column(db.Integer, db.ForeignKey('users7.id'))


class Event_records4(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String)
    event_desc = db.Column(db.String)
    event_type = db.Column(db.String)
    event_privacy = db.Column(db.String)
    data1 = db.Column(db.String)
    room_code = db.Column(db.String)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    creator_id = db.Column(db.Integer, db.ForeignKey('users7.id'))  # Link to the user who created it
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)


class Attendee_records3(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String)
    event_desc = db.Column(db.String)
    event_privacy = db.Column(db.String)
    date_accepted = db.Column(db.DateTime(timezone=True), default=func.now())
    attendee_id = db.Column(db.Integer, db.ForeignKey('users7.id'))  # Link to the attendee
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)


class Client_events6(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data1 = db.Column(db.String)  # Store data as JSON string
    event_name = db.Column(db.String)
    event_type = db.Column(db.String)
    event_desc = db.Column(db.String)  # Add event description
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users7.id'))
    max_attendee_num = db.Column(db.Integer)  # Add max attendees
    start_date = db.Column(db.DateTime)  # Add start time/date
    end_date = db.Column(db.DateTime)  # Add end time/date

class Client_Hired_Suppliers3(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('client_events6.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users7.id'), nullable=False)  # Link to the user who accepted the request
    supplier_fullname = db.Column(db.String, nullable=False)
    supplier_type = db.Column(db.String, nullable=False)
    commission = db.Column(db.String, nullable=False)
    phone_number = db.Column(db.Integer, nullable=False)
    phone_number2 = db.Column(db.Integer, nullable=True)
    email_sup = db.Column(db.String, nullable=False)
    supplier_description = db.Column(db.String, nullable=True)
    extra_info = db.Column(db.String, nullable=True)
    over_all_rating = db.Column(db.String, nullable=True)

    event = db.relationship('Client_events6', backref='client_hired_suppliers3')
    user = db.relationship('Users7', backref='client_hired_suppliers3')  # Backref to Users7

class Supplier_info8(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String)
    supplier_type = db.Column(db.String)
    commission = db.Column(db.String)
    phone_number = db.Column(db.Integer)
    phone_number2 = db.Column(db.Integer)
    email_sup = db.Column(db.String)
    supplier_description = db.Column(db.String)
    extra_info = db.Column(db.String)
    over_all_rating = db.Column(db.String)
    reviewer = db.Column(db.String)
    rating = db.Column(db.String)
    feedback = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('users7.id'))


class Supplier_Req_Jobs3(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier_info8.id'), nullable=False)
    req_event_creator = db.Column(db.String, nullable=False)
    req_event_name = db.Column(db.String, nullable=False)
    req_event_type = db.Column(db.String, nullable=False)
    req_room_code = db.Column(db.String, nullable=False)
    req_start_date = db.Column(db.DateTime, nullable=False)
    req_end_date = db.Column(db.DateTime, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('users7.id'))  # Add client_id

    supplier = db.relationship('Supplier_info8', backref='supplier_requests_jobs')


class SupplierJobs3(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier_info8.id'), nullable=False)
    job_event_creator = db.Column(db.String, nullable=False)
    job_event_name = db.Column(db.String, nullable=False)
    job_event_type = db.Column(db.String, nullable=False)
    job_room_code = db.Column(db.String, nullable=False)
    job_start_date = db.Column(db.DateTime, nullable=False)
    job_end_date = db.Column(db.DateTime, nullable=False)

    supplier = db.relationship('Supplier_info8', backref='supplier_jobs')


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users7.id'))
