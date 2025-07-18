# Terminal Setup Guide

## Current Environment
- Shell: `/bin/bash`
- Terminal: `xterm-256color`
- User: `guci`
- Home: `/home/guci`

## Quick Setup Commands

### 1. Enhanced Bash Configuration
Add these to your `~/.bashrc`:

```bash
# Better command history
export HISTSIZE=10000
export HISTFILESIZE=20000
export HISTCONTROL=ignoredups:erasedups
shopt -s histappend

# Useful aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'
alias grep='grep --color=auto'
alias df='df -h'
alias du='du -h'

# Git aliases
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gd='git diff'
alias gl='git log --oneline --graph --decorate'

# Python development
alias py='python3'
alias pip='pip3'
alias venv='python3 -m venv'
alias activate='source venv/bin/activate'

# Project navigation
alias cdproject='cd ~/aiProjects/AgentFrameWork'
alias cdcog='cd ~/aiProjects/AgentFrameWork/embodied_cognitive_workflow'

# Enhanced prompt with git branch
parse_git_branch() {
    git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/(\1)/'
}
export PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\[\033[01;31m\]$(parse_git_branch)\[\033[00m\]\$ '
```

### 2. Install Terminal Enhancements

```bash
# Install useful tools
sudo apt-get update
sudo apt-get install -y tmux htop tree ncdu ripgrep fd-find bat

# Install starship prompt (optional, modern prompt)
curl -sS https://starship.rs/install.sh | sh

# Install zsh and oh-my-zsh (optional, enhanced shell)
sudo apt-get install -y zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

### 3. Tmux Configuration
Create `~/.tmux.conf`:

```bash
# Enable mouse support
set -g mouse on

# Better colors
set -g default-terminal "screen-256color"

# Start windows and panes at 1, not 0
set -g base-index 1
setw -g pane-base-index 1

# Easier split commands
bind | split-window -h
bind - split-window -v

# Reload config
bind r source-file ~/.tmux.conf \; display "Config reloaded!"

# Status bar
set -g status-bg black
set -g status-fg white
set -g status-left '#[fg=green]#S '
set -g status-right '#[fg=yellow]%Y-%m-%d %H:%M'
```

### 4. VS Code Terminal Integration
Add to VS Code settings.json:

```json
{
    "terminal.integrated.defaultProfile.linux": "bash",
    "terminal.integrated.fontSize": 14,
    "terminal.integrated.fontFamily": "'Fira Code', 'Consolas', 'monospace'",
    "terminal.integrated.cursorBlinking": true,
    "terminal.integrated.cursorStyle": "line",
    "terminal.integrated.scrollback": 10000
}
```

### 5. Environment Variables for Your Project
Add to `~/.bashrc`:

```bash
# Project environment
export AGENT_PROJECT="$HOME/aiProjects/AgentFrameWork"
export PYTHONPATH="$AGENT_PROJECT:$PYTHONPATH"

# Proxy settings (already in your files)
export http_proxy="http://127.0.0.1:7890"
export https_proxy="http://127.0.0.1:7890"
export no_proxy="localhost,127.0.0.1"

# API Keys (if needed)
# export OPENAI_API_KEY="your-key-here"
# export ANTHROPIC_API_KEY="your-key-here"
```

## Quick Commands to Apply Settings

```bash
# 1. Backup current .bashrc
cp ~/.bashrc ~/.bashrc.backup

# 2. Apply basic enhancements
cat >> ~/.bashrc << 'EOF'

# === Terminal Enhancements ===
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

# Project shortcuts
alias cdproject='cd ~/aiProjects/AgentFrameWork'
alias cdcog='cd ~/aiProjects/AgentFrameWork/embodied_cognitive_workflow'

# Git shortcuts
alias gs='git status'
alias gd='git diff'
alias gl='git log --oneline --graph --decorate'
EOF

# 3. Reload bashrc
source ~/.bashrc
```

## Recommended Terminal Emulators

1. **Default Terminal**: Works fine with above configurations
2. **Terminator**: Advanced split-screen features
   ```bash
   sudo apt-get install terminator
   ```
3. **Tilix**: Modern tiling terminal
   ```bash
   sudo apt-get install tilix
   ```

## Project-Specific Setup

For your Embodied Cognitive Workflow project:

```bash
# Create a project activation script
cat > ~/aiProjects/AgentFrameWork/activate.sh << 'EOF'
#!/bin/bash
# Activate project environment

echo "🚀 Activating Embodied Cognitive Workflow Environment"

# Set project root
export PROJECT_ROOT="$(dirname "$(readlink -f "$0")")"
cd $PROJECT_ROOT

# Activate Python virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Python venv activated"
fi

# Set Python path
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Show project status
echo "📁 Project: $PROJECT_ROOT"
echo "🐍 Python: $(which python3)"
echo "📦 Pip: $(which pip3)"

# Optional: Show git status
if [ -d ".git" ]; then
    echo "📊 Git status:"
    git status -s
fi

echo "✨ Environment ready!"
EOF

chmod +x ~/aiProjects/AgentFrameWork/activate.sh
```

## Usage

1. Apply basic settings:
   ```bash
   source ~/.bashrc
   ```

2. Navigate to project:
   ```bash
   cdproject  # Goes to ~/aiProjects/AgentFrameWork
   ```

3. Activate project environment:
   ```bash
   ./activate.sh
   ```

## Tips

- Use `Ctrl+R` to search command history
- Use `Tab` for auto-completion
- Use `!!` to repeat last command
- Use `!$` to use last argument of previous command
- Use `cd -` to go to previous directory

---
Generated: 2025-01-18