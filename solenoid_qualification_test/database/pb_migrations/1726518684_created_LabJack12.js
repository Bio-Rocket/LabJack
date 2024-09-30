/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const collection = new Collection({
    "id": "axf7rvr084k750y",
    "created": "2024-09-16 20:31:24.835Z",
    "updated": "2024-09-16 20:31:24.835Z",
    "name": "LabJack12",
    "type": "base",
    "system": false,
    "schema": [
      {
        "system": false,
        "id": "cxafhn6z",
        "name": "pt_data",
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
    "listRule": "",
    "viewRule": "",
    "createRule": "",
    "updateRule": "",
    "deleteRule": "",
    "options": {}
  });

  return Dao(db).saveCollection(collection);
}, (db) => {
  const dao = new Dao(db);
  const collection = dao.findCollectionByNameOrId("axf7rvr084k750y");

  return dao.deleteCollection(collection);
})
