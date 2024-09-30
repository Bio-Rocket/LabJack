/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("zcplkg93frolshb")

  // update
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "yfdhtzqo",
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
  }))

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("zcplkg93frolshb")

  // update
  collection.schema.addField(new SchemaField({
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
  }))

  return dao.saveCollection(collection)
})
