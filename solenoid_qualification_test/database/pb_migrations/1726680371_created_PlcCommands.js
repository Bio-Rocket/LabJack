/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const collection = new Collection({
    "id": "wi9q8kr9qpi4i1w",
    "created": "2024-09-18 17:26:11.765Z",
    "updated": "2024-09-18 17:26:11.765Z",
    "name": "PlcCommands",
    "type": "base",
    "system": false,
    "schema": [
      {
        "system": false,
        "id": "ah1tjwts",
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
  const collection = dao.findCollectionByNameOrId("wi9q8kr9qpi4i1w");

  return dao.deleteCollection(collection);
})
