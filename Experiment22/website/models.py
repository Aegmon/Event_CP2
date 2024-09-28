from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Users2(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    role = db.Column(db.String(50))  # New column for role
    notes = db.relationship('Note')
    events = db.relationship('Events8')
    attend = db.relationship('Attendee_events5')
    client_events = db.relationship('Client_events4')
    supplier_info = db.relationship('Supplier_info')

class Events8(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data1 = db.Column(db.String)  # Store data as JSON string
    event_name = db.Column(db.String)
    event_desc = db.Column(db.String)  # New column for event description
    event_type = db.Column(db.String)
    event_privacy = db.Column(db.String)  # New column for event status
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users2.id'))
    invited_attendees = db.Column(db.Text)
    rsvp_attendees = db.Column(db.String)
    max_attendee_num = db.Column(db.Integer)  # New column for max attendees
    start_date = db.Column(db.DateTime)  # New column for start time/date
    end_date = db.Column(db.DateTime)  # New column for end time/date

class Attendee_events5(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invites = db.Column(db.Text)  # Store data as JSON string
    rsvp_events = db.Column(db.Text)
    attending_events = db.Column(db.Text)
    rejected_invites = db.Column(db.Text)  # New column to store rejected invites and reasons
    user_id = db.Column(db.Integer, db.ForeignKey('users2.id'))

class Event_records2(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String)
    event_desc = db.Column(db.String)
    event_type = db.Column(db.String)
    event_privacy = db.Column(db.String)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    creator_id = db.Column(db.Integer, db.ForeignKey('users2.id'))  # Link to the user who created it
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)

class Attendee_records2(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String)
    event_desc = db.Column(db.String)
    event_privacy = db.Column(db.String)
    date_accepted = db.Column(db.DateTime(timezone=True), default=func.now())
    attendee_id = db.Column(db.Integer, db.ForeignKey('users2.id'))  # Link to the attendee
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)

class Client_events4(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data1 = db.Column(db.String)  # Store data as JSON string
    event_name = db.Column(db.String)
    event_type = db.Column(db.String)
    event_desc = db.Column(db.String)  # Add event description
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users2.id'))
    max_attendee_num = db.Column(db.Integer)  # Add max attendees
    start_date = db.Column(db.DateTime)  # Add start time/date
    end_date = db.Column(db.DateTime)  # Add end time/date

class Supplier_info(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_type = db.Column(db.String)  # Store data as JSON string
    av_commission = db.Column(db.String)
    nickname = db.Column(db.String)
    phone_number = db.Column(db.String)
    email_sup = db.Column(db.String)
    video_chatting_id = db.Column(db.String)
    self_desc = db.Column(db.String)
    extra_info = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('users2.id'))

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users2.id'))