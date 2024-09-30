/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const collection = new Collection({
    "id": "54y5kw94ejfy9hp",
    "created": "2024-09-16 20:38:25.101Z",
    "updated": "2024-09-16 20:38:25.101Z",
    "name": "LabJack2",
    "type": "base",
    "system": false,
    "schema": [
      {
        "system": false,
        "id": "2uzoobll",
        "name": "lj2_data",
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
  const collection = dao.findCollectionByNameOrId("54y5kw94ejfy9hp");

  return dao.deleteCollection(collection);
})
