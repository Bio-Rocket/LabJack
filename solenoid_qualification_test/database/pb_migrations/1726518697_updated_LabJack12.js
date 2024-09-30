/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("axf7rvr084k750y")

  collection.name = "LabJack1"

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("axf7rvr084k750y")

  collection.name = "LabJack12"

  return dao.saveCollection(collection)
})
