/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const collection = new Collection({
    "id": "oachconmz651x2y",
    "created": "2024-09-16 20:39:49.745Z",
    "updated": "2024-09-16 20:39:49.745Z",
    "name": "PidOutput",
    "type": "base",
    "system": false,
    "schema": [
      {
        "system": false,
        "id": "mutztgzw",
        "name": "valve_1_state",
        "type": "bool",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {}
      },
      {
        "system": false,
        "id": "cxvssvhq",
        "name": "valve_2_state",
        "type": "bool",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {}
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
  const collection = dao.findCollectionByNameOrId("oachconmz651x2y");

  return dao.deleteCollection(collection);
})
