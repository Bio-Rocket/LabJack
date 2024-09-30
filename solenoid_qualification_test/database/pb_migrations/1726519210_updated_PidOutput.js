/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("oachconmz651x2y")

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "ik7yejfs",
    "name": "valve_3_state",
    "type": "bool",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {}
  }))

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("oachconmz651x2y")

  // remove
  collection.schema.removeField("ik7yejfs")

  return dao.saveCollection(collection)
})
