#!/usr/bin/env python3
"""
Setup Google Cloud Authentication
Prompts for credentials and sets up authentication for the correct account.
"""

import os
import subprocess
import sys


def check_current_auth():
    """Check current authentication status."""
    print("🔍 Checking current authentication...")
    
    try:
        # Check current account
        result = subprocess.run(['gcloud', 'auth', 'list', '--filter=status:ACTIVE', '--format=value(account)'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            current_account = result.stdout.strip()
            print(f"✓ Currently authenticated as: {current_account}")
            return current_account
        else:
            print("❌ No active authentication found")
            return None
    except Exception as e:
        print(f"❌ Error checking authentication: {e}")
        return None


def check_current_project():
    """Check current project."""
    try:
        result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip() != "(unset)":
            project = result.stdout.strip()
            print(f"✓ Current project: {project}")
            return project
        else:
            print("❌ No project set")
            return None
    except Exception as e:
        print(f"❌ Error checking project: {e}")
        return None


def authenticate_new_account():
    """Authenticate with a new Google account."""
    print("\n🔐 Setting up authentication for new account...")
    
    # Login with gcloud
    print("Opening browser for Google Cloud authentication...")
    try:
        result = subprocess.run(['gcloud', 'auth', 'login'], check=True)
        print("✅ Authentication successful!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Authentication failed: {e}")
        return False
    
    # Set up application default credentials
    print("\nSetting up Application Default Credentials...")
    try:
        result = subprocess.run(['gcloud', 'auth', 'application-default', 'login'], check=True)
        print("✅ Application Default Credentials set!")
    except subprocess.CalledProcessError as e:
        print(f"❌ ADC setup failed: {e}")
        return False
    
    return True


def select_project():
    """Select or set a Google Cloud project."""
    print("\n📋 Setting up project...")
    
    # List available projects
    try:
        result = subprocess.run(['gcloud', 'projects', 'list', '--format=value(projectId)'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            projects = [p.strip() for p in result.stdout.strip().split('\n') if p.strip()]
            if projects:
                print(f"Available projects:")
                for i, project in enumerate(projects, 1):
                    print(f"  {i}. {project}")
                
                while True:
                    try:
                        choice = input(f"\nSelect project (1-{len(projects)}) or enter project ID manually: ").strip()
                        
                        # Check if it's a number (selection)
                        if choice.isdigit():
                            idx = int(choice) - 1
                            if 0 <= idx < len(projects):
                                selected_project = projects[idx]
                                break
                            else:
                                print(f"Invalid selection. Please choose 1-{len(projects)}")
                        else:
                            # Assume it's a project ID
                            selected_project = choice
                            break
                    except KeyboardInterrupt:
                        print("\n❌ Cancelled")
                        return None
            else:
                selected_project = input("No projects found. Enter project ID: ").strip()
        else:
            selected_project = input("Enter project ID: ").strip()
    except Exception as e:
        print(f"Error listing projects: {e}")
        selected_project = input("Enter project ID: ").strip()
    
    if not selected_project:
        print("❌ No project specified")
        return None
    
    # Set the project
    try:
        subprocess.run(['gcloud', 'config', 'set', 'project', selected_project], check=True)
        print(f"✅ Project set to: {selected_project}")
        return selected_project
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to set project: {e}")
        return None


def enable_required_apis(project_id):
    """Enable required APIs for the project."""
    print(f"\n🔧 Enabling required APIs for project {project_id}...")
    
    required_apis = [
        'aiplatform.googleapis.com',
        'bigquery.googleapis.com',
        'storage.googleapis.com',
        'cloudbuild.googleapis.com'
    ]
    
    for api in required_apis:
        print(f"Enabling {api}...")
        try:
            subprocess.run(['gcloud', 'services', 'enable', api], check=True)
            print(f"✅ {api} enabled")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Failed to enable {api}: {e}")
    
    print("✅ API enablement completed")


def verify_setup():
    """Verify the authentication setup."""
    print("\n🧪 Verifying setup...")
    
    # Check authentication
    current_account = check_current_auth()
    if not current_account:
        return False
    
    # Check project
    current_project = check_current_project()
    if not current_project:
        return False
    
    # Test BigQuery access
    print("Testing BigQuery access...")
    try:
        subprocess.run(['bq', 'ls', '--max_results=1'], check=True, capture_output=True)
        print("✅ BigQuery access verified")
    except subprocess.CalledProcessError:
        print("⚠️  BigQuery access test failed (this might be normal if no datasets exist)")
    
    # Test Vertex AI access
    print("Testing Vertex AI access...")
    try:
        result = subprocess.run(['gcloud', 'ai', 'models', 'list', '--region=us-central1', '--limit=1'], 
                              check=True, capture_output=True)
        print("✅ Vertex AI access verified")
    except subprocess.CalledProcessError:
        print("⚠️  Vertex AI access test failed")
    
    return True


def main():
    """Main setup function."""
    print("🚀 Google Cloud Authentication Setup")
    print("=" * 50)
    
    # Check current status
    current_account = check_current_auth()
    current_project = check_current_project()
    
    # Ask if user wants to change account
    if current_account:
        change_account = input(f"\nCurrently authenticated as: {current_account}\nDo you want to authenticate with a different account? (y/N): ").strip().lower()
        if change_account in ['y', 'yes']:
            if not authenticate_new_account():
                return 1
        else:
            print("Keeping current authentication")
    else:
        print("No authentication found. Setting up new authentication...")
        if not authenticate_new_account():
            return 1
    
    # Set up project
    if current_project:
        change_project = input(f"\nCurrent project: {current_project}\nDo you want to change project? (y/N): ").strip().lower()
        if change_project in ['y', 'yes']:
            project = select_project()
            if not project:
                return 1
        else:
            project = current_project
    else:
        project = select_project()
        if not project:
            return 1
    
    # Enable APIs
    enable_apis = input(f"\nEnable required APIs for project {project}? (Y/n): ").strip().lower()
    if enable_apis not in ['n', 'no']:
        enable_required_apis(project)
    
    # Verify setup
    if verify_setup():
        print("\n✅ Authentication setup completed successfully!")
        print(f"Account: {check_current_auth()}")
        print(f"Project: {check_current_project()}")
        print("\n🚀 You can now run: python deploy_simple.py")
        return 0
    else:
        print("\n❌ Setup verification failed")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)
