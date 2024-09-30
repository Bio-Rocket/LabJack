/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const collection = new Collection({
    "id": "zcplkg93frolshb",
    "created": "2024-09-16 20:38:45.077Z",
    "updated": "2024-09-16 20:38:45.077Z",
    "name": "LabJack1Commands",
    "type": "base",
    "system": false,
    "schema": [
      {
        "system": false,
        "id": "yfdhtzqo",
        "name": "Command",
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
  const collection = dao.findCollectionByNameOrId("zcplkg93frolshb");

  return dao.deleteCollection(collection);
})
