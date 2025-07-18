#!/bin/bash
# Activate Embodied Cognitive Workflow Environment

echo "🧠 Activating Embodied Cognitive Workflow Environment"
echo "=" * 50

# Set project root
export PROJECT_ROOT="$(dirname "$(readlink -f "$0")")"
cd $PROJECT_ROOT

# Set Python path
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Set proxy (if needed)
export http_proxy="http://127.0.0.1:7890"
export https_proxy="http://127.0.0.1:7890"

# Activate Python virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Python venv activated"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Python .venv activated"
else
    echo "ℹ️  No virtual environment found"
fi

# Show environment info
echo ""
echo "📁 Project Root: $PROJECT_ROOT"
echo "🐍 Python: $(which python3) ($(python3 --version))"
echo "📦 Pip: $(which pip3)"
echo ""

# Show git status
if [ -d ".git" ]; then
    echo "📊 Git Status:"
    git status -s
    echo ""
fi

# Show quick commands
echo "🚀 Quick Commands:"
echo "  runvisual    - Run visual debugger"
echo "  rundemo      - Run demo examples"
echo "  cdproject    - Go to project root"
echo "  cdcog        - Go to cognitive workflow directory"
echo ""
echo "✨ Environment ready! Happy coding! 🎉"
