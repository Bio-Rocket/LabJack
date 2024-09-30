/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const collection = new Collection({
    "id": "epgquow8rs4unht",
    "created": "2024-09-18 17:09:58.882Z",
    "updated": "2024-09-18 17:09:58.882Z",
    "name": "PLC",
    "type": "base",
    "system": false,
    "schema": [
      {
        "system": false,
        "id": "mmdukauu",
        "name": "plc_data",
        "type": "json",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "maxSize": 2000000
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
  const collection = dao.findCollectionByNameOrId("epgquow8rs4unht");

  return dao.deleteCollection(collection);
})
