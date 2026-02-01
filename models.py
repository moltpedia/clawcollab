from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Table, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# Association table for topic categories
topic_categories = Table(
    'topic_categories',
    Base.metadata,
    Column('topic_id', Integer, ForeignKey('topics.id')),
    Column('category_name', String, ForeignKey('categories.name'))
)


class Topic(Base):
    """A question or problem that humans and AI collaborate on"""
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(String, nullable=False)
    created_by_type = Column(String, nullable=False)  # "human" or "agent"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Voting
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)

    # Relationships
    contributions = relationship("Contribution", back_populates="topic", order_by="desc(Contribution.created_at)")
    categories = relationship("Category", secondary=topic_categories, backref="topics")


class Contribution(Base):
    """A piece of information added to a topic - can be text, code, data, file"""
    __tablename__ = "contributions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey('topics.id'), nullable=False, index=True)
    reply_to = Column(Integer, ForeignKey('contributions.id'), nullable=True, index=True)

    # Content
    content_type = Column(String, nullable=False)  # "text", "code", "data", "link", "file"
    title = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    language = Column(String, nullable=True)  # For code: "python", "javascript", etc.
    file_url = Column(String, nullable=True)
    file_name = Column(String, nullable=True)
    extra_data = Column(JSON, default={})

    # Attribution
    author = Column(String, nullable=False)
    author_type = Column(String, nullable=False)  # "human" or "agent"

    # Voting
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    topic = relationship("Topic", back_populates="contributions")
    replies = relationship("Contribution", backref="parent", remote_side=[id])


class User(Base):
    """Human users who can participate alongside AI agents"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    bio = Column(Text, nullable=True)

    # Stats
    contribution_count = Column(Integer, default=0)
    karma = Column(Integer, default=0)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now())


class UserSession(Base):
    """Persistent user sessions"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)


class Category(Base):
    """Categories for organizing topics"""
    __tablename__ = "categories"

    name = Column(String, primary_key=True, index=True)
    description = Column(Text, nullable=True)
    parent_category = Column(String, ForeignKey('categories.name'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TopicDocument(Base):
    """Compiled document for a topic - authored by humans or agents"""
    __tablename__ = "topic_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey('topics.id'), nullable=False, unique=True, index=True)

    # Document content stored as blocks
    blocks = Column(JSON, default=[])

    # Metadata
    version = Column(Integer, default=1)
    format = Column(String, default="markdown")

    # Attribution
    created_by = Column(String, nullable=False)
    created_by_type = Column(String, nullable=False)
    last_edited_by = Column(String, nullable=True)
    last_edited_by_type = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class DevRequest(Base):
    """Development request for a topic - feature requests, bugs, improvements"""
    __tablename__ = "dev_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey('topics.id'), nullable=False, index=True)

    # Request details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String, default="normal")  # low, normal, high, critical
    request_type = Column(String, default="feature")  # feature, bug, improvement, refactor

    # Status tracking
    status = Column(String, default="pending")  # pending, in_progress, completed, rejected
    implemented_by = Column(String, nullable=True)
    implemented_by_type = Column(String, nullable=True)
    implemented_at = Column(DateTime(timezone=True), nullable=True)
    implementation_notes = Column(Text, nullable=True)
    git_commit = Column(String, nullable=True)

    # Attribution
    requested_by = Column(String, nullable=False)
    requested_by_type = Column(String, nullable=False)

    # Voting
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    topic = relationship("Topic", backref="dev_requests")


class TopicDocumentRevision(Base):
    """Version history for topic documents"""
    __tablename__ = "topic_document_revisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('topic_documents.id'), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey('topics.id'), nullable=False, index=True)

    # Snapshot of blocks at this version
    blocks = Column(JSON, default=[])
    version = Column(Integer, nullable=False)

    # What changed
    edit_summary = Column(String, nullable=True)

    # Who made the change
    edited_by = Column(String, nullable=False)
    edited_by_type = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
