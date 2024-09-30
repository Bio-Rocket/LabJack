/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const collection = new Collection({
    "id": "q8cz0c7hfe6extq",
    "created": "2024-09-16 20:39:04.135Z",
    "updated": "2024-09-16 20:39:04.135Z",
    "name": "LabJack2Commands",
    "type": "base",
    "system": false,
    "schema": [
      {
        "system": false,
        "id": "vos78vuy",
        "name": "command",
        "type": "text",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "min": null,
          "max": null,
          "pattern": ""
        }
      }
    ],
    "indexes": [],
    "listRule": null,
    "viewRule": null,
    "createRule": null,
    "updateRule": null,
    "deleteRule": null,
    "options": {}
  });

  return Dao(db).saveCollection(collection);
}, (db) => {
  const dao = new Dao(db);
  const collection = dao.findCollectionByNameOrId("q8cz0c7hfe6extq");

  return dao.deleteCollection(collection);
})
