/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("oachconmz651x2y")

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "7cez4kux",
    "name": "valve_4_state",
    "type": "bool",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {}
  }))

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "kmvcpf06",
    "name": "error",
    "type": "number",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "min": null,
      "max": null,
      "noDecimal": false
    }
  }))

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "fpxjambe",
    "name": "setpoint",
    "type": "number",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "min": null,
      "max": null,
      "noDecimal": false
    }
  }))

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("oachconmz651x2y")

  // remove
  collection.schema.removeField("7cez4kux")

  // remove
  collection.schema.removeField("kmvcpf06")

  // remove
  collection.schema.removeField("fpxjambe")

  return dao.saveCollection(collection)
})
