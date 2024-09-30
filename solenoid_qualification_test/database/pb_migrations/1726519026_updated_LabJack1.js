/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("axf7rvr084k750y")

  // update
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "cxafhn6z",
    "name": "lj1_data",
    "type": "json",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "maxSize": 2000000
    }
  }))

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("axf7rvr084k750y")

  // update
  collection.schema.addField(new SchemaField({
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
  }))

  return dao.saveCollection(collection)
})
