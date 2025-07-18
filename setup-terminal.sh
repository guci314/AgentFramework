#!/bin/bash
# Terminal Setup Script for Embodied Cognitive Workflow Project

echo "🚀 Setting up terminal enhancements..."

# Check if enhancements already added
if grep -q "Terminal Enhancements (Added by Claude)" ~/.bashrc; then
    echo "✅ Terminal enhancements already installed"
else
    echo "📝 Adding terminal enhancements to ~/.bashrc"
    
    cat >> ~/.bashrc << 'TERMINAL_EOF'

# === Terminal Enhancements (Added by Claude) ===
# Better history
export HISTSIZE=10000
export HISTFILESIZE=20000
export HISTCONTROL=ignoredups:erasedups
shopt -s histappend

# Useful aliases
alias ll='ls -alF'
alias la='ls -A'
alias ..='cd ..'
alias ...='cd ../..'
alias grep='grep --color=auto'

# Project shortcuts
alias cdproject='cd ~/aiProjects/AgentFrameWork'
alias cdcog='cd ~/aiProjects/AgentFrameWork/embodied_cognitive_workflow'

# Git shortcuts
alias gs='git status'
alias gd='git diff'
alias gl='git log --oneline --graph --decorate'
alias glog='git log --oneline --graph --decorate --all'

# Python shortcuts
alias py='python3'
alias pip='pip3'
alias venv='python3 -m venv'
alias activate='source venv/bin/activate'

# Project-specific functions
runvisual() {
    cd ~/aiProjects/AgentFrameWork
    python3 embodied_cognitive_workflow/visual_debugger.py "$@"
}

rundemo() {
    cd ~/aiProjects/AgentFrameWork
    python3 embodied_cognitive_workflow/demo/demo_visual_debugger_usage.py "$@"
}
TERMINAL_EOF

    echo "✅ Terminal enhancements added!"
fi

# Create project activation script
echo "📝 Creating project activation script..."

cat > ~/aiProjects/AgentFrameWork/activate.sh << 'ACTIVATE_EOF'
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
ACTIVATE_EOF

chmod +x ~/aiProjects/AgentFrameWork/activate.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "To apply the changes:"
echo "  1. Run: source ~/.bashrc"
echo "  2. Or open a new terminal"
echo ""
echo "To activate project environment:"
echo "  cd ~/aiProjects/AgentFrameWork && ./activate.sh"
echo ""
echo "📖 See terminal-setup.md for more details"