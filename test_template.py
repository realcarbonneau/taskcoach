#!/usr/bin/env python3
"""Test template save/load functionality"""

import sys
import os
import tempfile
import shutil

# Add taskcoach to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from taskcoachlib.domain.task import Task
from taskcoachlib.persistence.templatelist import TemplateList

def test_template_save_load():
    """Test saving and loading a simple template"""

    # Create a temporary directory for templates
    temp_dir = tempfile.mkdtemp()
    print(f"Testing in: {temp_dir}")

    try:
        # Create a simple task
        task = Task(subject="Test Task")
        task.setPlannedStartDateTime(None)
        task.setDueDateTime(None)

        print(f"\n1. Created task: {task.subject()}")

        # Create template list
        templates = TemplateList(temp_dir)
        print(f"2. Created TemplateList")

        # Add template
        print(f"3. Adding template...")
        theTask = templates.addTemplate(task)
        print(f"4. Template added: {theTask.subject()}")

        # Save templates
        print(f"5. Saving templates...")
        templates.save()
        print(f"6. Templates saved")

        # Load templates again
        print(f"7. Loading templates from disk...")
        templates2 = TemplateList(temp_dir)
        print(f"8. Loaded {len(templates2)} templates")

        if len(templates2) > 0:
            loaded_task = templates2.tasks()[0]
            print(f"9. Loaded task subject: {loaded_task.subject()}")
            print("\n✓ SUCCESS: Template save/load works!")
            return True
        else:
            print("\n✗ FAILED: No templates loaded")
            return False

    except Exception as e:
        print(f"\n✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"\nCleaned up: {temp_dir}")

if __name__ == "__main__":
    success = test_template_save_load()
    sys.exit(0 if success else 1)
