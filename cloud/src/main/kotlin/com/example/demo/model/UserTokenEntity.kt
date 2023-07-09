package com.example.demo.model

import com.fasterxml.jackson.annotation.JsonManagedReference
import jakarta.persistence.*
import jakarta.persistence.GenerationType.IDENTITY

@Entity
@Table(name = "user_token", schema = "demo")
class UserTokenEntity (
    @Id
    @GeneratedValue(strategy = IDENTITY)
    @Column(name = "id", nullable = false)
    var id: Long? = 0,

    @Column(name = "token", nullable = false)
    val token: String? = null
) {
    @OneToMany(mappedBy = "userToken")
    @JsonManagedReference
    val edgeData: Set<EdgeDataEntity> = setOf()
}