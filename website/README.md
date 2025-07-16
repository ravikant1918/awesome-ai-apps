# Hugo Website Documentation

This directory contains the Hugo static site generator setup for the Awesome AI Apps website.

## 🚀 Quick Start

### Prerequisites

- [Hugo Extended](https://gohugo.io/getting-started/installing/) v0.146.0 or higher
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rohitg00/awesome-ai-apps.git
   cd awesome-ai-apps/website
   ```

2. **Install Python dependencies:**
   ```bash
   pip install pyyaml
   ```

3. **Generate content from README:**
   ```bash
   python scripts/parse_readme.py --readme ../Readme.md --output .
   ```

4. **Start development server:**
   ```bash
   hugo server --bind 0.0.0.0 --port 1313
   ```

5. **Visit the site:**
   Open [http://localhost:1313/awesome-ai-apps/](http://localhost:1313/awesome-ai-apps/)

## 📁 Directory Structure

```
website/
├── archetypes/          # Content templates
├── assets/             # SCSS, JS, images
├── content/            # Markdown content files
│   ├── apps/           # Generated app pages
│   └── categories/     # Category pages
├── data/               # JSON data files
├── layouts/            # Hugo templates
│   ├── _default/       # Default layouts
│   └── partials/       # Reusable template parts
├── scripts/            # Build scripts
├── static/             # Static files
├── themes/             # Hugo themes
└── hugo.toml          # Hugo configuration
```

## 🛠️ Content Management

### Adding New Applications

The content is automatically generated from the main `Readme.md` file. To add a new application:

1. **Edit the main README.md** in the repository root
2. **Add your application** in the appropriate category section
3. **Run the content generator:**
   ```bash
   cd website
   python scripts/parse_readme.py --readme ../Readme.md --output .
   ```
4. **Build and test:**
   ```bash
   hugo server
   ```

### Manual Content Updates

If you need to manually update content:

1. **Application pages** are in `content/apps/[category]/[app-name].md`
2. **Category pages** are in `content/categories/[category-name].md`
3. **Data files** are in `data/apps.json` and `data/categories.json`

### Theme Configuration

The site uses the [PaperMod](https://github.com/adityatelange/hugo-PaperMod) theme with custom layouts:

- **Homepage:** `layouts/_default/home.html`
- **Apps listing:** `layouts/_default/list.html`
- **App detail:** `layouts/_default/single.html`

## 🚀 Deployment

### Automatic Deployment (Recommended)

The site automatically deploys to GitHub Pages when:
- Changes are pushed to the `main` branch
- The `Readme.md` file is updated
- Files in the `website/` directory are modified

### Manual Deployment

1. **Generate content:**
   ```bash
   python scripts/parse_readme.py --readme ../Readme.md --output .
   ```

2. **Build the site:**
   ```bash
   hugo --minify
   ```

3. **Deploy to GitHub Pages:**
   The built site will be in the `public/` directory. The GitHub Action will handle deployment automatically.

### Local Build

To build the site locally:

```bash
# Clean build
hugo --minify

# Build with draft content
hugo --buildDrafts

# Build for production
hugo --minify --environment production
```

## 🔧 Configuration

### Hugo Configuration (`hugo.toml`)

Key configuration options:

```toml
baseURL = 'https://rohitg00.github.io/awesome-ai-apps/'
languageCode = 'en-us'
title = 'Awesome AI Apps'
theme = 'PaperMod'
```

### Theme Configuration

The PaperMod theme is configured with:
- Custom homepage layout
- Navigation menu
- Social icons
- Search functionality
- Dark/light theme toggle

## 📝 Content Generation Script

The `scripts/parse_readme.py` script:

1. **Parses** the main README.md file
2. **Extracts** application information by category
3. **Generates** Hugo content files
4. **Creates** data files for filtering
5. **Updates** category pages

### Script Usage

```bash
python scripts/parse_readme.py --readme ../Readme.md --output .
```

### Supported Categories

- Starter Agents
- Advanced Agents
- Multi-Agent Teams
- RAG Applications
- Multimodal Apps

## 🎨 Customization

### Styling

Custom styles are included in the layout files:
- Homepage styles in `layouts/_default/home.html`
- App grid styles in `layouts/_default/list.html`

### Layout Modifications

To customize layouts:

1. **Copy theme layouts** to `layouts/` directory
2. **Modify** the copied files
3. **Test** with `hugo server`

### Adding New Features

1. **Create new layouts** in `layouts/`
2. **Add assets** in `assets/`
3. **Update configuration** in `hugo.toml`
4. **Test thoroughly** before deploying

## 🔍 Troubleshooting

### Common Issues

1. **Hugo version mismatch:** Ensure you're using Hugo Extended v0.146.0+
2. **Content not updating:** Run the content generation script
3. **Theme not loading:** Check that submodules are properly initialized
4. **Build errors:** Check Hugo logs for specific errors

### Debug Commands

```bash
# Check Hugo version
hugo version

# Verbose build
hugo --verbose

# Check site configuration
hugo config

# List all pages
hugo list all
```

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** locally with `hugo server`
5. **Submit** a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🙏 Acknowledgments

- [Hugo](https://gohugo.io/) - Static site generator
- [PaperMod](https://github.com/adityatelange/hugo-PaperMod) - Hugo theme
- [GitHub Actions](https://github.com/features/actions) - CI/CD
- [GitHub Pages](https://pages.github.com/) - Hosting