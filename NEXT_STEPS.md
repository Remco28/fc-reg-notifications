# Next Steps for Fencing Club Registration Notifications

## Milestone 1: Core Data Pipeline
- [x] Implement database models (`Tournament`, `Fencer`, `Registration`)
- [x] Implement CRUD functions for data persistence
- [x] Implement scraper for `fencingtracker.com`
- [x] Integrate scraper with CRUD functions to persist data and detect changes
- [x] Set up basic application entrypoint (`main.py`) to run the scraper

## Future Enhancements (Backlog)
- [ ] Add email notification system for new/updated registrations
- [ ] Build a simple web UI to display registrations
- [ ] Add scraper for `askfred.net`
- [ ] Implement job scheduling with APScheduler

## Documentation
- [ ] Write API documentation (initial version via FastAPI)
- [ ] Add setup and usage instructions to a `README.md`