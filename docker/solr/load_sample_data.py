#!/usr/bin/env python3
"""
Sample data loader for Apache Solr in the testing environment.

This script uploads sample documents to the Solr server for development and testing.
"""
import json
import datetime
import requests
from typing import List, Dict, Any


def get_sample_documents() -> List[Dict[str, Any]]:
    """
    Generate sample document data for testing.
    
    Returns:
        List[Dict[str, Any]]: List of sample documents
    """
    now = datetime.datetime.now().isoformat() + "Z"
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat() + "Z"
    
    return [
        {
            "id": "doc1",
            "title": "Introduction to Apache Solr",
            "content": "Apache Solr is an open-source search platform built on Apache Lucene.",
            "category": "technology",
            "author": "John Smith",
            "created_date": yesterday,
            "last_modified": now
        },
        {
            "id": "doc2",
            "title": "Machine Learning Basics",
            "content": "Machine learning is a method of data analysis that automates analytical model building.",
            "category": "technology",
            "author": "Jane Doe",
            "created_date": yesterday,
            "last_modified": now
        },
        {
            "id": "doc3",
            "title": "Python Programming Guide",
            "content": "Python is an interpreted, high-level, general-purpose programming language.",
            "category": "programming",
            "author": "John Smith",
            "created_date": yesterday,
            "last_modified": now
        },
        {
            "id": "doc4",
            "title": "Data Structures and Algorithms",
            "content": "A data structure is a particular way of organizing data in a computer.",
            "category": "programming",
            "author": "Alice Johnson",
            "created_date": yesterday,
            "last_modified": now
        },
        {
            "id": "doc5",
            "title": "Web Development with JavaScript",
            "content": "JavaScript is a programming language used to create dynamic content for websites.",
            "category": "programming",
            "author": "Bob Brown",
            "created_date": yesterday,
            "last_modified": now
        },
        {
            "id": "doc6",
            "title": "Database Design Principles",
            "content": "Database design is the process of producing a detailed data model of a database.",
            "category": "database",
            "author": "Carol White",
            "created_date": yesterday,
            "last_modified": now
        },
        {
            "id": "doc7",
            "title": "Introduction to Docker",
            "content": "Docker is a platform for developing, shipping, and running applications in containers.",
            "category": "devops",
            "author": "David Green",
            "created_date": yesterday,
            "last_modified": now
        },
        {
            "id": "doc8",
            "title": "RESTful API Design",
            "content": "REST is an architectural style for designing networked applications.",
            "category": "api",
            "author": "Emma Black",
            "created_date": yesterday,
            "last_modified": now
        },
        {
            "id": "doc9",
            "title": "Cloud Computing Fundamentals",
            "content": "Cloud computing is the on-demand delivery of IT resources over the Internet.",
            "category": "cloud",
            "author": "Frank Gray",
            "created_date": yesterday,
            "last_modified": now
        },
        {
            "id": "doc10",
            "title": "Artificial Intelligence Overview",
            "content": "Artificial intelligence is the simulation of human intelligence in machines.",
            "category": "technology",
            "author": "Grace Lee",
            "created_date": yesterday,
            "last_modified": now
        }
    ]


def load_documents_to_solr(solr_url: str, documents: List[Dict[str, Any]]) -> bool:
    """
    Load the sample documents to Solr.
    
    Args:
        solr_url (str): URL of the Solr collection
        documents (List[Dict[str, Any]]): List of documents to load
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Add documents to Solr
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.post(
            f"{solr_url}/update?commitWithin=1000", 
            headers=headers, 
            data=json.dumps(documents)
        )
        response.raise_for_status()
        
        # Commit the changes
        commit_response = requests.get(f"{solr_url}/update?commit=true")
        commit_response.raise_for_status()
        
        print(f"Successfully loaded {len(documents)} documents to Solr")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error loading documents to Solr: {e}")
        return False


def main():
    """Main function to load sample data."""
    solr_url = "http://localhost:8983/solr/documents"
    documents = get_sample_documents()
    success = load_documents_to_solr(solr_url, documents)
    
    if success:
        print("Sample data loaded successfully!")
    else:
        print("Failed to load sample data.")


if __name__ == "__main__":
    main()