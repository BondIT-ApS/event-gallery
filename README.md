# 🧱 Event Gallery

[![Build Status](https://img.shields.io/github/actions/workflow/status/BondIT-ApS/event-gallery/docker-publish.yml?branch=main&style=for-the-badge)](https://github.com/BondIT-ApS/event-gallery/actions)
[![License](https://img.shields.io/github/license/BondIT-ApS/event-gallery?style=for-the-badge)](LICENSE)
[![Repo Size](https://img.shields.io/github/repo-size/BondIT-ApS/event-gallery?style=for-the-badge)](https://github.com/BondIT-ApS/event-gallery)
[![Made in Denmark](https://img.shields.io/badge/made%20in-Denmark%20🇩🇰-red?style=for-the-badge)](https://bondit.dk)
[![Powered by Coffee](https://img.shields.io/badge/powered%20by-coffee%20☕-brown?style=for-the-badge)](https://bondit.dk)

## 📸 Building Better Events, One Photo at a Time

Welcome to Event Gallery - where we do for event photo sharing what LEGO did for children's toys: make it more structured, easier to work with, and way more fun to explore! 

Just like building a LEGO masterpiece, we've crafted a solution that assembles event photos into something greater than the sum of its parts. This mobile-friendly, containerized solution provides simple access control, automatic organization, and admin features with precision and elegance. Built with Python/Flask for reliable photo sharing that just works.

## 🚀 Features - The Building Blocks

- **📱 Mobile-Friendly Upload** – Works seamlessly with "Take Photo/Video" on phones, like having the right LEGO pieces at your fingertips
- **🔐 Simple Access Control** – EVENT_CODE for guests and ADMIN_CODE for organizers, as secure as a LEGO vault
- **💾 Smart Storage Organization** – Stores originals by date/guest with automatic filename deduplication, like sorting LEGO bricks by color and set
- **📦 Admin Download Center** – Download everything as a ZIP file, like getting your complete LEGO collection in one box
- **🖼️ Optional Public Gallery** – Can be enabled or disabled based on event privacy needs
- **⚙️ Sensible Configuration** – Environment-based config for ports, size limits, and more
- **🐳 Single Container Deployment** – Deployable via Portainer Stack or Container, as easy as following a LEGO instruction manual

## 🧱 Getting Started - The Foundation Pieces

### Prerequisites - Tools You'll Need

- [Docker](https://www.docker.com/get-started) - Your primary building tool
- [Docker Compose](https://docs.docker.com/compose/install/) - For connecting the pieces

### Installation - Assembly Instructions

1. **📦 Clone the repository**:
    ```bash
    git clone https://github.com/BondIT-ApS/event-gallery.git
    cd event-gallery
    ```

2. **⚙️ Configure Your Build**:
    Update the `.env` file with your event settings:
    ```env
    # Copy the template first
    cp .env.template .env
    
    # Then edit with your settings
    EVENT_CODE=your_guest_access_code
    ADMIN_CODE=your_admin_access_code
    MAX_FILE_SIZE=50MB
    PORT=8080
    ```

3. **🚀 Assemble the Solution**:
    ```bash
    docker-compose up -d
    ```
    Just like that final satisfying "click" when LEGO pieces connect, your container is now running!

4. **🎯 Access Your Gallery**:
    - **Upload Page**: http://localhost:8080
    - **Admin Panel**: http://localhost:8080/admin
    - **Public Gallery**: http://localhost:8080/gallery (if enabled)

## 📱 How It Works - Playing with Your Creation

- **Guest Access**: Users enter the EVENT_CODE to upload photos from their mobile devices
- **Mobile Upload**: Native support for phone cameras with "Take Photo/Video" functionality
- **Automatic Organization**: Photos are organized by date and guest, with duplicate filenames handled automatically
- **Admin Control**: Event organizers use ADMIN_CODE to access admin features and download all photos
- **Privacy First**: Public gallery can be disabled for private events

## 🧰 Project Architecture - The Building Design

Just like a well-designed LEGO set, this solution consists of several key components:

1. **Flask Application** - The foundation pieces that handle uploads and gallery display
2. **File Storage System** - The stable baseplate that organizes all your photos
3. **Access Control** - The security mechanisms that protect your event
4. **Docker Container** - The instruction manual that makes deployment a breeze

## 👷‍♂️ Contributing - Join Our Building Team

Contributions are welcome! Feel free to open an issue or submit a pull request. Like any good LEGO enthusiast, we believe more builders create better creations.

1. Fork the repository (like borrowing a few bricks)
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request (show us your creation!)

## 📄 License - The Building Rules

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 
Like LEGO, you're free to rebuild and reimagine as you see fit!

---

## 🏢 About BondIT ApS

This project is maintained by [BondIT ApS](https://bondit.dk), a Danish IT consultancy that builds digital solutions one brick at a time. Just like our fellow Danish company LEGO, we believe in building things methodically, with precision and a touch of playfulness. Because the best solutions, like the best LEGO creations, are both functional AND fun!

**Made with ❤️, ☕, and 🧱 by BondIT ApS**